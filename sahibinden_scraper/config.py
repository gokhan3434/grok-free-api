"""Configuration utilities for the Sahibinden scraper."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class ProxySettings:
    """Container describing proxy options for HTTP requests."""

    http: Optional[str] = None
    https: Optional[str] = None

    def as_requests_proxies(self) -> Dict[str, str]:
        """Return a dictionary that can be consumed by :mod:`requests`.

        Returns an empty dictionary when no proxies are configured.
        """

        proxies: Dict[str, str] = {}
        if self.http:
            proxies["http"] = self.http
        if self.https:
            proxies["https"] = self.https
        return proxies


@dataclass
class ScraperConfig:
    """Runtime settings for :class:`~sahibinden_scraper.scraper.SahibindenScraper`."""

    base_url: str = "https://www.sahibinden.com"
    listing_path: str = "emlak"
    rate_limit_seconds: Tuple[float, float] = (2.0, 5.0)
    max_listings: int = 100
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
    output_directory: Path = field(default_factory=lambda: Path.cwd() / "exports")
    log_file: Path = field(default_factory=lambda: Path.cwd() / "logs" / "scraper.log")
    verify_robots: bool = True
    use_selenium: bool = False


@dataclass
class SearchFilters:
    """Structured representation of supported search filters."""

    city: str = ""
    district: str = ""
    listing_type: str = "satilik"  # satilik, kiralik, vb.
    property_type: str = ""  # apartment, villa, land, etc.
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    room_count: Optional[str] = None
    area_min: Optional[int] = None
    area_max: Optional[int] = None
    exclude_keywords: Iterable[str] = field(default_factory=tuple)
    exclude_urgent: bool = False
    include_photos: bool = False

    def to_query_params(self) -> Dict[str, str]:
        """Translate search filters to sahibinden.com query parameters.

        The public site uses query parameters such as ``pagingOffset`` and
        ``pagingSize``. Since sahibinden.com frequently changes these parameters,
        the method keeps the mapping in a single place so the scraper can be
        updated quickly when required.
        """

        params: Dict[str, str] = {}
        if self.city:
            params["city"] = self.city
        if self.district:
            params["district"] = self.district
        if self.listing_type:
            params["listingType"] = self.listing_type
        if self.property_type:
            params["propertyType"] = self.property_type
        if self.price_min is not None:
            params["price_min"] = str(self.price_min)
        if self.price_max is not None:
            params["price_max"] = str(self.price_max)
        if self.room_count:
            params["roomCount"] = self.room_count
        if self.area_min is not None:
            params["area_min"] = str(self.area_min)
        if self.area_max is not None:
            params["area_max"] = str(self.area_max)
        if self.include_photos:
            params["photo"] = "1"
        return params

    def excluded_terms(self) -> List[str]:
        """Return the list of keywords that must not appear in a listing."""

        terms: List[str] = []
        if self.exclude_urgent:
            terms.append("acil")
        terms.extend([term.lower() for term in self.exclude_keywords])
        return terms


__all__ = ["ProxySettings", "ScraperConfig", "SearchFilters"]
