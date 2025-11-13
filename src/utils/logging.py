"""
Logging Configuration

Configures structured logging for the application with console
and file handlers, colored output, and proper formatting.

Example:
    >>> from src.utils.logging import setup_logging
    >>> logger = setup_logging(verbose=True)
    >>> logger.info("Processing started")
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record):
        """Format log record with colors."""
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{self.BOLD}"
                f"{record.levelname:8s}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False,
    colored: bool = True,
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        verbose: Enable verbose (DEBUG) logging
        quiet: Suppress console output (only errors)
        colored: Enable colored console output

    Returns:
        Configured logger instance
    """
    # Determine log level
    if verbose:
        log_level = logging.DEBUG
    elif quiet:
        log_level = logging.ERROR
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Formatters
    if colored and sys.stdout.isatty():
        console_format = '%(asctime)s %(levelname)s %(message)s'
        console_formatter = ColoredFormatter(
            console_format,
            datefmt='%H:%M:%S'
        )
    else:
        console_format = '%(asctime)s [%(levelname)s] %(message)s'
        console_formatter = logging.Formatter(
            console_format,
            datefmt='%H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file

        file_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        file_formatter = logging.Formatter(
            file_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
