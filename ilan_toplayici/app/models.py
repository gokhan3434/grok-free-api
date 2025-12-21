"""Data models for the scraping workflow."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ScrapeConfig:
    listing_url: str
    max_pages: int
    min_delay: float
    max_delay: float
    fetch_details: bool
    only_with_contact: bool
    category_hint: Optional[str] = None
    user_data_dir: Optional[Path] = None
    remote_debugging_url: Optional[str] = None


@dataclass
class ListingRecord:
    ilan_no: Optional[str]
    baslik: str
    fiyat: Optional[str]
    metrekare: Optional[str]
    konum: Optional[str]
    il: Optional[str]
    ilce: Optional[str]
    mahalle: Optional[str]
    ilan_tarihi: Optional[str]
    ilan_tipi: Optional[str]
    tur: Optional[str]
    ilan_sahibi_tipi: Optional[str]
    ilan_sahibi_adi: Optional[str]
    telefon: Optional[str]
    mesaj: Optional[str]
    link: str
    aciklama: Optional[str] = None
    profil_link: Optional[str] = None

    @classmethod
    def headers(cls) -> List[str]:
        return [
            "İlan No",
            "Başlık",
            "Fiyat",
            "m²",
            "İl",
            "İlçe",
            "Mahalle",
            "İlan Tarihi",
            "İlan Tipi",
            "Tür",
            "İlan Sahibi Tipi",
            "İlan Sahibi / Ofis",
            "Telefon",
            "Mesajlaşma Var mı",
            "Link",
            "Açıklama",
            "Profil Linki",
        ]

    def as_row(self) -> Dict[str, Optional[str]]:
        return {
            "İlan No": self.ilan_no or "",
            "Başlık": self.baslik,
            "Fiyat": self.fiyat or "",
            "m²": self.metrekare or "",
            "İl": self.il or "",
            "İlçe": self.ilce or "",
            "Mahalle": self.mahalle or "",
            "İlan Tarihi": self.ilan_tarihi or "",
            "İlan Tipi": self.ilan_tipi or "",
            "Tür": self.tur or "",
            "İlan Sahibi Tipi": self.ilan_sahibi_tipi or "",
            "İlan Sahibi / Ofis": self.ilan_sahibi_adi or "",
            "Telefon": self.telefon or "",
            "Mesajlaşma Var mı": self.mesaj or "",
            "Link": self.link,
            "Açıklama": self.aciklama or "",
            "Profil Linki": self.profil_link or "",
        }


@dataclass
class ScrapeStats:
    total_found: int = 0
    processed: int = 0
    failed: int = 0
    remaining: int = 0
    log_lines: List[str] = field(default_factory=list)

    def as_progress_tuple(self) -> tuple[int, int, int, int]:
        return self.total_found, self.processed, self.failed, self.remaining
