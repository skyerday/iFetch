import logging
import sys
from typing import Optional


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger for the application.

    Args:
        log_file: Optional path to a log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('icloud_downloader')
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Always add console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
