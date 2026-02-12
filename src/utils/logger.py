"""Logging utility for application."""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "XPlaneSceneryTool", log_to_file: bool = True) -> logging.Logger:
    """Set up application logger.

    Args:
        name: Logger name
        log_to_file: Whether to log to file

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        log_dir = Path.home() / ".xplane_scenery_tool" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger()
