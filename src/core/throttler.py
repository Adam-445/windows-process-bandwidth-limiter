"""
Core network throttling engine.

This module contains the main NetworkThrottler class that orchestrates
all throttling operations, including packet capture, bandwidth limiting,
and latency simulation.
"""

import logging
import random
import threading
import time
from contextlib import contextmanager
from typing import Optional, Set

import pydivert

from ..config.settings import ThrottlingConfig
from ..utils.bandwidth_limiter import BandwidthLimiter
from ..utils.keyboard_handler import KeyboardHandler
from ..utils.process_manager import ProcessManager
from ..utils.statistics import ThrottlingStatistics

logger = logging.getLogger(__name__)


class NetworkThrottler:
    """Main network throttling engine."""

    def __init__(self, config: ThrottlingConfig):
        """Initialize the network throttler.

        Args:
            config: Configuration object containing all settings
        """
        self.config = config
        self.process_manager = ProcessManager()
        self.bandwidth_limiter = BandwidthLimiter(config.max_bytes_per_second)
        self.statistics = ThrottlingStatistics()
        self.keyboard_handler = KeyboardHandler(config)

        # Threading controls
        self._throttling_enabled = False
        self._throttling_lock = threading.Lock()
        self._shutdown_event = threading.Event()

        # Process information
        self._target_pid: Optional[int] = None
        self._target_ports: Set[int] = set()

        logger.info(f"NetworkThrottler initialized with config: {config}")

    @property
    def throttling_enabled(self) -> bool:
        """Check if throttling is currently enabled."""
        with self._throttling_lock:
            return self._throttling_enabled

    def toggle_throttling(self) -> None:
        """Toggle throttling on/off."""
        with self._throttling_lock:
            self._throttling_enabled = not self._throttling_enabled
            status = "ENABLED" if self._throttling_enabled else "DISABLED"

            logger.info(f"Throttling {status}")
            print(
                f"\nThrottling {status} - Press {self.config.toggle_key.upper()} to toggle"
            )

            if self._throttling_enabled:
                print(f"{self.config.process_name_substring} will now be throttled")
            else:
                print(f"{self.config.process_name_substring} throttling removed")

    def shutdown(self) -> None:
        """Gracefully shutdown the throttler."""
        logger.info("Initiating shutdown...")
        self._shutdown_event.set()

        # Stop keyboard handler
        self.keyboard_handler.stop()

        # Log final statistics
        self.statistics.log_final_stats()

        logger.info("Shutdown complete")

    def _initialize_target_process(self) -> None:
        """Find and initialize the target process."""
        try:
            self._target_pid = self.process_manager.find_process_by_name(
                self.config.process_name_substring
            )
            logger.info(
                f"Found {self.config.process_name_substring} process PID={self._target_pid}"
            )

            # Get ports used by the process
            self._target_ports = self.process_manager.get_process_ports(
                self._target_pid
            )
            logger.info(
                f"{self.config.process_name_substring} is using ports: {self._target_ports}"
            )

        except RuntimeError as e:
            logger.error(f"Failed to find target process: {e}")
            print(f"Error: {e}")
            print(
                f"Make sure {self.config.process_name_substring} is running and try again."
            )
            raise

    def _setup_keyboard_handler(self) -> None:
        """Setup keyboard event handling."""
        self.keyboard_handler.register_callback(
            self.config.toggle_key, self.toggle_throttling
        )
        self.keyboard_handler.register_callback(self.config.exit_key, self.shutdown)
        self.keyboard_handler.start()

        print(f"Press {self.config.toggle_key.upper()} to toggle throttling ON/OFF")
        print("Press ESC to exit")

    def _should_drop_packet(self) -> bool:
        """Determine if a packet should be dropped based on drop rate."""
        return random.random() < self.config.packet_drop_rate

    def _apply_throttling(self, packet_size: int) -> None:
        """Apply throttling effects to a packet.

        Args:
            packet_size: Size of the packet in bytes
        """
        # Apply bandwidth limiting
        self.bandwidth_limiter.throttle(packet_size)

        # Add artificial delay for latency simulation
        if self.config.lag_delay_ms > 0:
            time.sleep(self.config.lag_delay_seconds)

    def _process_packet(self, packet, windivert_handle) -> None:
        """Process a single packet through the throttling pipeline.

        Args:
            packet: The captured packet
            windivert_handle: WinDivert handle for sending packets
        """
        packet_size = len(packet.raw)
        self.statistics.increment_processed()

        # Check if throttling is enabled
        should_throttle = self.throttling_enabled

        if should_throttle:
            self.statistics.increment_throttled()

            # Check for packet drop
            if self._should_drop_packet():
                self.statistics.increment_dropped()
                logger.debug(f"Dropped packet of size {packet_size} bytes")
                return  # Don't forward this packet

            # Apply throttling effects
            self._apply_throttling(packet_size)

        # Forward the packet
        windivert_handle.send(packet)

        # Update statistics and log status
        self._update_status(should_throttle)

    def _update_status(self, throttling_active: bool) -> None:
        """Update and display status information.

        Args:
            throttling_active: Whether throttling is currently active
        """
        if self.statistics.processed_packets % self.config.status_update_interval == 0:
            status = "THROTTLING" if throttling_active else "NORMAL"
            current_rate = self.bandwidth_limiter.get_current_rate_kbps()

            print(
                f"{status} | "
                f"Processed: {self.statistics.processed_packets} | "
                f"Throttled: {self.statistics.throttled_packets} | "
                f"Dropped: {self.statistics.dropped_packets} | "
                f"Rate: {current_rate:.1f} KB/s"
            )

    @contextmanager
    def _packet_capture_context(self):
        """Context manager for packet capture operations."""
        try:
            MAX_LISTED_PORTS = 20
            start, end = self.config.port_range_start, self.config.port_range_end

            if self._target_ports and len(self._target_ports) <= MAX_LISTED_PORTS:
                port_conditions = " or ".join(
                    f"tcp.SrcPort == {p} or tcp.DstPort == {p} or udp.SrcPort == {p} or udp.DstPort == {p}"
                    for p in self._target_ports
                )
                filter_str = f"(tcp or udp) and ({port_conditions})"

            else:
                # Too many (or zero) specific ports: just do the full range
                filter_str = (
                    "(tcp or udp) and "
                    f"((tcp.DstPort >= {start} and tcp.DstPort <= {end}) or "
                    f"(udp.DstPort >= {start} and udp.DstPort <= {end}))"
                )

            with pydivert.WinDivert(filter_str) as windivert_handle:
                logger.info("Packet capture started successfully")
                yield windivert_handle

        except Exception as e:
            logger.error(f"Packet capture error: {e}")
            
            if self._target_ports and "parameter is incorrect" in str(e):
                logger.info("Complex filter failed, trying simpler approach...")
                try:
                    limited_ports = list(self._target_ports)[:5]
                    port_conditions = " or ".join([
                        f"tcp.SrcPort == {port} or tcp.DstPort == {port} or "
                        f"udp.SrcPort == {port} or udp.DstPort == {port}"
                        for port in limited_ports
                    ])
                    simple_filter = f"(tcp or udp) and ({port_conditions})"
                    
                    logger.info(f"Trying simplified filter: {simple_filter}")
                    with pydivert.WinDivert(simple_filter) as windivert_handle:
                        logger.info("Packet capture started with simplified filter")
                        yield windivert_handle
                        return
                except Exception as e2:
                    logger.error(f"Simplified filter also failed: {e2}")
            
            # If all else fails, try the most basic filter
            try:
                basic_filter = "tcp or udp"
                logger.info(f"Trying basic filter: {basic_filter}")
                with pydivert.WinDivert(basic_filter) as windivert_handle:
                    logger.info("Packet capture started with basic filter")
                    yield windivert_handle
                    return
            except Exception as e3:
                logger.error(f"Even basic filter failed: {e3}")
            
            raise

    def run(self) -> None:
        """Main execution loop for the network throttler."""
        try:
            # Initialize target process
            self._initialize_target_process()

            # Setup keyboard handling
            self._setup_keyboard_handler()

            # Display initial information
            print(
                f"Throttling settings: {self.config.target_bandwidth_mbps} Mbps, "
                f"{self.config.lag_delay_ms}ms delay, "
                f"{self.config.packet_drop_rate*100}% packet loss"
            )

            print("Starting packet capture...")

            # Main packet processing loop
            with self._packet_capture_context() as windivert_handle:
                for packet in windivert_handle:
                    # Check for shutdown signal
                    if self._shutdown_event.is_set():
                        break

                    # Process the packet
                    self._process_packet(packet, windivert_handle)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            print(f"\nThrottling stopped by user")

        except Exception as e:
            logger.error(f"Runtime error: {e}")
            print(f"Error: {e}")
            self._print_troubleshooting_info()
            raise

        finally:
            self.shutdown()

    def _print_troubleshooting_info(self) -> None:
        """Print troubleshooting information for common issues."""
        print("\nTroubleshooting:")
        print("1. Make sure you're running as administrator")
        print("2. Check if WinDivert.dll is in the same directory")
        print("3. Verify WinDivert.dll matches your Python architecture (x64/x86)")
        print("4. Try restarting the process and running the script again")
        print("5. Check Windows Defender/antivirus settings")
        print("6. Ensure no other packet capture tools are running")
        print("7. Try reducing the number of target ports if the filter is too complex")