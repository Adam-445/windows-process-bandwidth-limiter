"""
Configuration management for the Network Throttling Tool.

This module handles all configuration settings, validation, and provides
a centralized way to manage application parameters.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ThrottlingConfig:
    """Configuration class for network throttling parameters."""

    # Core throttling settings
    target_bandwidth_mbps: float = 2.0
    lag_delay_ms: int = 10
    packet_drop_rate: float = 0.0

    # Process targeting
    process_name_substring: str = "Your-process-here"

    # Control settings
    toggle_key: str = "f1"
    exit_key: str = "esc"

    # Technical settings
    status_update_interval: int = 100  # packets
    port_range_start: int = 49000
    port_range_end: int = 65000

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_settings()

    def _validate_settings(self) -> None:
        """Validate all configuration settings."""
        if self.target_bandwidth_mbps <= 0:
            raise ValueError("Target bandwidth must be positive")

        if self.lag_delay_ms < 0:
            raise ValueError("Lag delay cannot be negative")

        if not 0 <= self.packet_drop_rate <= 1:
            raise ValueError("Packet drop rate must be between 0 and 1")

        if self.status_update_interval <= 0:
            raise ValueError("Status update interval must be positive")

        if self.port_range_start >= self.port_range_end:
            raise ValueError("Port range start must be less than end")

    @property
    def max_bytes_per_second(self) -> float:
        """Calculate maximum bytes per second from Mbps setting."""
        return self.target_bandwidth_mbps * 1_000_000 / 8

    @property
    def lag_delay_seconds(self) -> float:
        """Convert lag delay from milliseconds to seconds."""
        return self.lag_delay_ms / 1000.0

    @classmethod
    def from_file(cls, config_path: Path) -> "ThrottlingConfig":
        """Load configuration from JSON file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Configuration loaded from {config_path}")
            return cls(**data)

        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def save_to_file(self, config_path: Path) -> None:
        """Save current configuration to JSON file."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)

            logger.info(f"Configuration saved to {config_path}")

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    def update_settings(self, **kwargs) -> None:
        """Update configuration settings dynamically."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated {key} to {value}")
            else:
                logger.warning(f"Unknown configuration key: {key}")

        self._validate_settings()

    def get_windivert_filter(self, ports: set) -> str:
        """Generate WinDivert filter string based on configuration."""
        if ports:
            port_conditions = " or ".join(
                [
                    f"tcp.SrcPort == {port} or tcp.DstPort == {port} or "
                    f"udp.SrcPort == {port} or udp.DstPort == {port}"
                    for port in ports
                ]
            )
            return f"(tcp or udp) and ({port_conditions})"
        else:
            return (
                "(tcp or udp) and "
                "((tcp.DstPort >= 49000 and tcp.DstPort <= 65000) or "
                "(udp.DstPort >= 49000 and udp.DstPort <= 65000))"
            )

    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"ThrottlingConfig("
            f"bandwidth={self.target_bandwidth_mbps}Mbps, "
            f"delay={self.lag_delay_ms}ms, "
            f"drop_rate={self.packet_drop_rate*100}%, "
            f"process='{self.process_name_substring}'"
            f")"
        )
