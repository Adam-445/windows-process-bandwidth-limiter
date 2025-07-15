#!/usr/bin/env python3
"""
Network Throttling Tool
A professional-grade network throttling application for Windows.

This tool allows you to simulate network conditions (bandwidth limiting,
latency, packet loss) for specific processes, useful for testing applications
under various network conditions.

Author: Adam Achoubir
Version: 2.0.0
License: MIT
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.throttler import NetworkThrottler
from src.config.settings import ThrottlingConfig
from src.utils.admin_check import ensure_admin_privileges
from src.utils.logger import setup_logging


def main():
    """Main entry point for the Network Throttling Tool."""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Check admin privileges first
        ensure_admin_privileges()
        
        # Load configuration
        config = ThrottlingConfig()
        
        # Create and run the throttler
        throttler = NetworkThrottler(config)
        throttler.run()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()