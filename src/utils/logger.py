"""Logging configuration for RailOpt AI.

Provides structured, formatted console and file logging.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str = "RailOptAI", log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger.

    Args:
        name: Name of the logger, typically __name__ or module identifier.
        log_file: Optional path to output log file.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
