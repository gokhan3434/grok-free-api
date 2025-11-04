"""Core scraping logic for Sahibinden.com listings."""
from __future__ import annotations

import logging
import random
import time
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:  # Optional Selenium support
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except ImportError:  # pragma: no cover - selenium is optional at runtime
    webdriver = None
    ChromeOptions = None

from .config import ProxySettings, ScraperConfig, SearchFilters
from .export import export_dataframe
from .utils import ProgressCallback, any_term_in_text

LOGGER = logging.getLogger(__name__)


class ScraperError(RuntimeError):
    """Raised when scraping fails in a recoverable manner."""


@dataclass
class Listing:
    """Data model representing a Sahibinden listing."""

    listing_id: str
    title: str
    price: str
    location: str
    area: Optional[str]
    room_count: Optional[str]
    url: str
    publish_date: Optional[str]
    seller: Optional[str]
    photo_url: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "listing_id": self.listing_id,
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "area": self.area,
            "room_count": self.room_count,
            "url": self.url,
            "publish_date": self.publish_date,
            "seller": self.seller,
            "photo_url": self.photo_url,
        }


class SahibindenScraper:
    """High level interface that fetches and parses listings."""

    def __init__(
        self,
        config: Optional[ScraperConfig] = None,
        proxies: Optional[ProxySettings] = None,
    ) -> None:
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})
        self.proxies = proxies or ProxySettings()
        self._robots: Optional[urllib.robotparser.RobotFileParser] = None
        self._driver: Optional["webdriver.Chrome"] = None
        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        self.config.log_file.parent.mkdir(parents=True, exist_ok=True)

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            if self._driver:
                self._driver.quit()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_listings(
        self,
        filters: SearchFilters,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> pd.DataFrame:
        """Fetch listings matching ``filters`` and return them as a DataFrame."""

        listings: List[Listing] = []
        fetched = 0
        page = 1
        max_listings = self.config.max_listings

        LOGGER.info("Starting scrape with filters: %s", filters)
        while fetched < max_listings:
            batch = self._fetch_page(filters, page)
            if not batch:
                LOGGER.info("No listings returned for page %s; stopping.", page)
                break

            for listing in batch:
                if self._should_skip_listing(listing, filters.excluded_terms()):
                    continue
                listings.append(listing)
                fetched += 1
                if progress_callback:
                    progress_callback(fetched, max_listings)
                if fetched >= max_listings:
                    LOGGER.info("Reached max listings limit (%s).", max_listings)
                    break

            page += 1
            self._apply_rate_limit()

        LOGGER.info("Fetched %s listings in total.", len(listings))
        df = pd.DataFrame([listing.as_dict() for listing in listings])
        if not df.empty:
            df = df.drop_duplicates(subset=["listing_id", "url"], keep="first")
        return df

    def export_listings(
        self, df: pd.DataFrame, output_path: Optional[str] = None, to_excel: bool = True
    ) -> str:
        output_path = output_path or str(
            self.config.output_directory / "sahibinden_listings.xlsx"
        )
        path = export_dataframe(df, Path(output_path), to_excel=to_excel)
        LOGGER.info("Exported %s listings to %s", len(df), path)
        return str(path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_page(self, filters: SearchFilters, page: int) -> List[Listing]:
        """Fetch and parse a single result page."""

        url = self._build_search_url(filters, page)
        LOGGER.debug("Fetching page %s: %s", page, url)
        html = self._perform_request(url)
        listings = self._parse_listings(html)

        if not listings and page == 1:
            LOGGER.warning("İlk sayfada ilan bulunamadı.")
        return listings

    def _build_search_url(self, filters: SearchFilters, page: int) -> str:
        query_params = filters.to_query_params()
        query_params.update({"pagingOffset": (page - 1) * 20, "pagingSize": 20})

        path = f"/{filters.listing_type}-{self.config.listing_path}"
        url = urllib.parse.urljoin(self.config.base_url, path)
        return f"{url}?{urllib.parse.urlencode(query_params)}"

    def _perform_request(self, url: str) -> str:
        if self.config.verify_robots and not self._is_allowed(url):
            raise ScraperError("Robots.txt disallows scraping this resource.")

        if self.config.use_selenium:
            return self._fetch_with_selenium(url)

        try:
            response = self.session.get(
                url,
                timeout=20,
                proxies=self.proxies.as_requests_proxies(),
            )
        except requests.RequestException as exc:  # pragma: no cover - network errors
            raise ScraperError(f"HTTP isteği başarısız oldu: {exc}") from exc
        if response.status_code == 429:
            raise ScraperError("Received HTTP 429 (Too Many Requests). Slow down scraping.")
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # pragma: no cover - network errors
            raise ScraperError(f"HTTP {response.status_code} hatası: {exc}") from exc
        return response.text

    def _fetch_with_selenium(self, url: str) -> str:
        if webdriver is None or ChromeOptions is None:
            raise ScraperError("Selenium is not installed but use_selenium=True.")

        driver = self._ensure_driver()
        try:
            driver.get(url)
            time.sleep(2)
            return driver.page_source
        except Exception as exc:  # noqa: BLE001
            raise ScraperError(f"Selenium sayfayı yükleyemedi: {exc}") from exc

    def _parse_listings(self, html: str) -> List[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("#searchResultsTable")
        if table is None:
            raise ScraperError(
                "Sonuç tablosu bulunamadı. Site yapısı değişmiş olabilir."
            )
        rows = table.select("tbody tr")
        listings: List[Listing] = []
        for row in rows:
            if "class" in row.attrs and "searchResultsPromo" in row["class"]:
                continue
            link = row.select_one("td.searchResultsTitleValue a")
            if not link:
                continue
            listing_id = row.get("data-id") or link.get("href", "").split("-")[0]
            title = link.get_text(strip=True)
            price = row.select_one("td.searchResultsPriceValue").get_text(strip=True)
            location = " ".join(
                part.get_text(strip=True)
                for part in row.select("td.searchResultsLocationValue *")
            )
            area_cell = row.select_one("td.searchResultsAttributeValue")
            area = area_cell.get_text(strip=True) if area_cell else None
            room_cell = row.select("td.searchResultsAttributeValue")
            room = room_cell[1].get_text(strip=True) if len(room_cell) > 1 else None
            publish_date = None
            date_cell = row.select_one("td.searchResultsDateValue")
            if date_cell:
                publish_date = date_cell.get_text(strip=True)

            seller = None
            seller_cell = row.select_one("td.searchResultsOwnerTypeValue")
            if seller_cell:
                seller = seller_cell.get_text(strip=True)

            photo_link = row.select_one("img")
            photo_url = photo_link["src"] if photo_link and "src" in photo_link.attrs else None

            url = urllib.parse.urljoin(self.config.base_url, link.get("href", ""))
            listings.append(
                Listing(
                    listing_id=listing_id,
                    title=title,
                    price=price,
                    location=location,
                    area=area,
                    room_count=room,
                    url=url,
                    publish_date=publish_date,
                    seller=seller,
                    photo_url=photo_url,
                )
            )
        return listings

    def _is_allowed(self, url: str) -> bool:
        if not self.config.verify_robots:
            return True
        if not self._robots:
            robots_url = urllib.parse.urljoin(self.config.base_url, "/robots.txt")
            self._robots = urllib.robotparser.RobotFileParser()
            self._robots.set_url(robots_url)
            self._robots.read()
        path = urllib.parse.urlparse(url).path
        allowed = self._robots.can_fetch(self.config.user_agent, path)
        if not allowed:
            LOGGER.warning("Robots.txt disallows the path: %s", path)
        return allowed

    def _apply_rate_limit(self) -> None:
        low, high = self.config.rate_limit_seconds
        delay = random.uniform(low, high)
        LOGGER.debug("Sleeping for %.2f seconds to respect rate limits", delay)
        time.sleep(delay)

    @staticmethod
    def _should_skip_listing(listing: Listing, excluded_terms: Iterable[str]) -> bool:
        if any_term_in_text(listing.title, excluded_terms):
            return True
        if listing.seller and any_term_in_text(listing.seller, excluded_terms):
            return True
        return False

    def _ensure_driver(self):
        if self._driver:
            return self._driver

        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--user-agent={self.config.user_agent}")

        proxy_url = self.proxies.http or self.proxies.https
        if proxy_url:
            options.add_argument(f"--proxy-server={proxy_url}")

        self._driver = webdriver.Chrome(options=options)
        return self._driver


__all__ = ["Listing", "SahibindenScraper", "ScraperError"]
