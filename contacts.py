from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import List, Sequence

from utils import deduplicate_numbers


@dataclass
class ContactProcessingResult:
    total_records: int
    unique_numbers: List[str]
    duplicates: List[str]
    invalid_rows: List[int]


class ContactsProcessor:
    """Utility class for turning CSV uploads into sanitized contact lists."""

    PHONE_HEADER_CANDIDATES = ("phone", "phone_number", "number", "msisdn", "tel")

    def __init__(self, encoding: str = "utf-8-sig") -> None:
        self.encoding = encoding

    def _detect_phone_column(self, headers: Sequence[str]) -> str:
        lowered = [header.strip().lower() for header in headers]
        for candidate in self.PHONE_HEADER_CANDIDATES:
            if candidate in lowered:
                index = lowered.index(candidate)
                return headers[index]
        if len(headers) == 1:
            return headers[0]
        raise ValueError(
            "CSV dosyasında telefon numarası için bir kolon bulunamadı. Lütfen 'phone' veya 'phone_number' başlığı ekleyin."
        )

    def process_csv_bytes(self, data: bytes) -> ContactProcessingResult:
        text = data.decode(self.encoding)
        csv_reader = csv.reader(io.StringIO(text))
        try:
            headers = next(csv_reader)
        except StopIteration as exc:
            raise ValueError("Boş bir CSV yüklendi.") from exc

        phone_column = self._detect_phone_column(headers)
        phone_index = headers.index(phone_column)

        numbers: List[str] = []
        invalid_rows: List[int] = []
        for index, row in enumerate(csv_reader, start=2):
            try:
                number = row[phone_index]
            except IndexError:
                invalid_rows.append(index)
                continue
            numbers.append(number)

        unique, duplicates = deduplicate_numbers(numbers)
        return ContactProcessingResult(
            total_records=len(numbers),
            unique_numbers=unique,
            duplicates=duplicates,
            invalid_rows=invalid_rows,
        )


__all__ = ["ContactsProcessor", "ContactProcessingResult"]
