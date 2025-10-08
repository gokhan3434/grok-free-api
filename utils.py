from __future__ import annotations

import re
from typing import Iterable, List, Tuple


PHONE_NORMALIZATION_REGEX = re.compile(r"[^0-9+]")


def normalize_phone_number(raw_number: str) -> str:
    """Normalize a phone number by removing non-digit characters and ensuring a leading '+'."""
    if raw_number is None:
        return ""

    stripped = PHONE_NORMALIZATION_REGEX.sub("", raw_number).lstrip("0")
    if not stripped:
        return ""

    if not stripped.startswith("+"):
        stripped = "+" + stripped
    return stripped


def deduplicate_numbers(numbers: Iterable[str]) -> Tuple[List[str], List[str]]:
    """Return unique numbers in insertion order and a list of duplicates encountered."""
    seen = set()
    unique_numbers: List[str] = []
    duplicates: List[str] = []

    for number in numbers:
        normalized = normalize_phone_number(number)
        if not normalized:
            continue
        if normalized in seen:
            duplicates.append(normalized)
        else:
            seen.add(normalized)
            unique_numbers.append(normalized)

    return unique_numbers, duplicates
