"""Statistics tracking for network throttling."""

import time
import logging
from dataclasses import dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class ThrottlingStatistics:
    """Statistics for network throttling operations."""
    
    processed_packets: int = 0
    throttled_packets: int = 0
    dropped_packets: int = 0
    start_time: float = time.time()
    
    def increment_processed(self) -> None:
        """Increment processed packet count."""
        self.processed_packets += 1
    
    def increment_throttled(self) -> None:
        """Increment throttled packet count."""
        self.throttled_packets += 1
    
    def increment_dropped(self) -> None:
        """Increment dropped packet count."""
        self.dropped_packets += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        elapsed = time.time() - self.start_time
        return {
            'processed_packets': self.processed_packets,
            'throttled_packets': self.throttled_packets,
            'dropped_packets': self.dropped_packets,
            'packets_per_second': self.processed_packets / elapsed if elapsed > 0 else 0,
            'runtime_seconds': elapsed
        }
    
    def log_final_stats(self) -> None:
        """Log final statistics."""
        stats = self.get_stats()
        logger.info("Final Statistics:")
        logger.info(f"Total packets processed: {stats['processed_packets']}")
        logger.info(f"Total packets throttled: {stats['throttled_packets']}")
        logger.info(f"Total packets dropped: {stats['dropped_packets']}")
        logger.info(f"Average packets/second: {stats['packets_per_second']:.2f}")
        logger.info(f"Total runtime: {stats['runtime_seconds']:.1f} seconds")