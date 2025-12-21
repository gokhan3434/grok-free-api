"""Utility helpers for logging, configuration, and timing."""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"


def setup_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """Configure application logger.

    Args:
        log_file: Optional file path to write log output.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("ilan_toplayici")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(LOG_FORMAT)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger


def random_delay_seconds(min_delay: float, max_delay: float) -> float:
    """Return a random delay between boundaries."""
    min_d = max(min_delay, 0)
    max_d = max(max_delay, min_d)
    return random.uniform(min_d, max_d)


@dataclass
class Paths:
    base_dir: Path
    profile_dir: Path
    export_dir: Path

    @classmethod
    def default(cls, base: Optional[Path] = None) -> "Paths":
        base_dir = base or Path.home() / ".ilan_toplayici"
        export_dir = base_dir / "exports"
        profile_dir = base_dir / "profile"
        export_dir.mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        return cls(base_dir=base_dir, profile_dir=profile_dir, export_dir=export_dir)


DEFAULT_TIMEOUT = 25_000
