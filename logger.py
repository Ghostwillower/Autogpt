"""Central logging utilities for Ghosthand."""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "ghosthand.log"

_logger = None


def _init_logger() -> logging.Logger:
    logger = logging.getLogger("ghosthand")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        size_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=5
        )
        time_handler = TimedRotatingFileHandler(
            LOG_FILE, when="D", interval=1, backupCount=7
        )
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        for h in (size_handler, time_handler):
            h.setFormatter(formatter)
            logger.addHandler(h)
    return logger


def log(message: str, level: str = "INFO") -> None:
    """Log a message to the shared logfile."""
    global _logger
    if _logger is None:
        _logger = _init_logger()
    lvl = getattr(logging, level.upper(), logging.INFO)
    _logger.log(lvl, message)
