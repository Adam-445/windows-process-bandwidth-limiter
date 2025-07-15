"""
Bandwidth limiting functionality.

This module provides precise bandwidth limiting using a token bucket algorithm
with sliding window rate limiting for smooth traffic shaping.
"""

import time
import threading
import logging


logger = logging.getLogger(__name__)


class BandwidthLimiter:
    """Token bucket based bandwidth limiter with sliding window."""
    
    def __init__(self, max_bytes_per_second: float, window_size: float = 1.0):
        """Initialize the bandwidth limiter.
        
        Args:
            max_bytes_per_second: Maximum bytes per second allowed
            window_size: Time window size in seconds for rate calculation
        """
        self.max_bytes_per_second = max_bytes_per_second
        self.window_size = window_size
        
        # Token bucket parameters
        self.bucket_size = max_bytes_per_second  # Bucket can hold 1 second worth of data
        self.tokens = self.bucket_size
        self.last_refill = time.time()
        
        # Sliding window for rate calculation
        self.bytes_sent = 0
        self.window_start = time.time()
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"BandwidthLimiter initialized: {max_bytes_per_second} bytes/sec")
    
    def _refill_tokens(self) -> None:
        """Refill tokens in the bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            # Add tokens based on elapsed time
            tokens_to_add = elapsed * self.max_bytes_per_second
            self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
            self.last_refill = now
    
    def _reset_window_if_needed(self) -> None:
        """Reset the sliding window if enough time has passed."""
        now = time.time()
        if now - self.window_start >= self.window_size:
            self.window_start = now
            self.bytes_sent = 0
    
    def throttle(self, packet_size: int) -> None:
        """Apply bandwidth throttling to a packet.
        
        Args:
            packet_size: Size of the packet in bytes
        """
        with self._lock:
            self._refill_tokens()
            self._reset_window_if_needed()
            
            # Check if we need to throttle
            if self.bytes_sent + packet_size > self.max_bytes_per_second:
                # Calculate how long to wait
                now = time.time()
                time_remaining = self.window_size - (now - self.window_start)
                
                if time_remaining > 0:
                    logger.debug(f"Throttling: waiting {time_remaining:.3f}s for {packet_size} bytes")
                    time.sleep(time_remaining)
                    
                    # Reset window after waiting
                    self.window_start = time.time()
                    self.bytes_sent = 0
            
            # Account for the packet
            self.bytes_sent += packet_size
    
    def can_send(self, packet_size: int) -> bool:
        """Check if a packet can be sent without throttling.
        
        Args:
            packet_size: Size of the packet in bytes
            
        Returns:
            True if packet can be sent immediately, False otherwise
        """
        with self._lock:
            self._refill_tokens()
            return self.tokens >= packet_size
    
    def get_current_rate_kbps(self) -> float:
        """Get the current transmission rate in KB/s.
        
        Returns:
            Current rate in kilobytes per second
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.window_start
            
            if elapsed > 0:
                return (self.bytes_sent / elapsed) / 1024
            return 0.0
    
    def get_current_rate_mbps(self) -> float:
        """Get the current transmission rate in Mbps.
        
        Returns:
            Current rate in megabits per second
        """
        return (self.get_current_rate_kbps() * 8) / 1024
    
    def update_rate_limit(self, new_max_bytes_per_second: float) -> None:
        """Update the rate limit dynamically.
        
        Args:
            new_max_bytes_per_second: New maximum bytes per second
        """
        with self._lock:
            self.max_bytes_per_second = new_max_bytes_per_second
            self.bucket_size = new_max_bytes_per_second
            
            # Adjust tokens if new limit is lower
            if self.tokens > self.bucket_size:
                self.tokens = self.bucket_size
            
            logger.info(f"Rate limit updated to {new_max_bytes_per_second} bytes/sec")
    
    def reset(self) -> None:
        """Reset the bandwidth limiter state."""
        with self._lock:
            self.tokens = self.bucket_size
            self.last_refill = time.time()
            self.bytes_sent = 0
            self.window_start = time.time()
            
            logger.debug("BandwidthLimiter reset")
    
    def get_stats(self) -> dict:
        """Get current statistics.
        
        Returns:
            Dictionary containing current statistics
        """
        with self._lock:
            return {
                'max_bytes_per_second': self.max_bytes_per_second,
                'current_tokens': self.tokens,
                'bytes_sent_in_window': self.bytes_sent,
                'current_rate_kbps': self.get_current_rate_kbps(),
                'current_rate_mbps': self.get_current_rate_mbps(),
                'window_utilization': self.bytes_sent / self.max_bytes_per_second
            }


class AdaptiveBandwidthLimiter(BandwidthLimiter):
    """Adaptive bandwidth limiter that adjusts based on network conditions."""
    
    def __init__(self, max_bytes_per_second: float, adaptation_factor: float = 0.1):
        """Initialize the adaptive bandwidth limiter.
        
        Args:
            max_bytes_per_second: Initial maximum bytes per second
            adaptation_factor: How quickly to adapt (0-1)
        """
        super().__init__(max_bytes_per_second)
        self.adaptation_factor = adaptation_factor
        self.base_rate = max_bytes_per_second
        self.congestion_detected = False
        
        logger.info(f"AdaptiveBandwidthLimiter initialized with adaptation factor {adaptation_factor}")
    
    def detect_congestion(self) -> bool:
        """Detect network congestion based on current metrics.
        
        Returns:
            True if congestion is detected, False otherwise
        """
        stats = self.get_stats()
        
        # Simple congestion detection: if we're consistently at max utilization
        high_utilization = stats['window_utilization'] > 0.9
        
        if high_utilization != self.congestion_detected:
            self.congestion_detected = high_utilization
            logger.info(f"Congestion {'detected' if high_utilization else 'cleared'}")
        
        return self.congestion_detected
    
    def adapt_rate(self) -> None:
        """Adapt the rate limit based on current conditions."""
        if self.detect_congestion():
            # Reduce rate during congestion
            new_rate = self.max_bytes_per_second * (1 - self.adaptation_factor)
        else:
            # Gradually increase rate when no congestion
            new_rate = min(
                self.base_rate,
                self.max_bytes_per_second * (1 + self.adaptation_factor * 0.1)
            )
        
        if abs(new_rate - self.max_bytes_per_second) > self.base_rate * 0.01:
            self.update_rate_limit(new_rate)
    
    def throttle(self, packet_size: int) -> None:
        """Apply adaptive bandwidth throttling."""
        # Periodically adapt the rate
        if time.time() - self.window_start > 0.5:  # Adapt every 500ms
            self.adapt_rate()
        
        super().throttle(packet_size)