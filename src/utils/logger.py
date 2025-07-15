"""Custom logger configuration for the bandwidth limiter application."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    module_name: str = "bandwidth_limiter"
) -> None:
    """Configure the application's logging system.
    
    Args:
        log_level: Logging level as string (default: "INFO")
        log_file: Optional path to log file (default: None)
        module_name: Name of the root logger (default: "bandwidth_limiter")
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(numeric_level)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        try:
            # Ensure directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(numeric_level)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to setup file logging: {e}")
    
    logger.info(f"Logging initialized at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger, typically __name__
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"bandwidth_limiter.{name}")