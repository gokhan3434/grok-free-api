"""Shared helper functions for the scraping toolkit."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterable, Optional


def setup_logging(log_file: Path) -> None:
    """Configure the root logger to emit to both console and a log file."""

    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def any_term_in_text(text: str, terms: Iterable[str]) -> bool:
    """Return ``True`` when one of ``terms`` occurs in ``text`` (case-insensitive)."""

    normalized = text.lower()
    return any(term in normalized for term in terms)


ProgressCallback = Callable[[int, Optional[int]], None]
