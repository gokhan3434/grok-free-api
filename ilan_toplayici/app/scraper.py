"""Playwright-powered scraper that runs inside a QThread."""
from __future__ import annotations

import asyncio
import traceback
from datetime import datetime
from typing import List, Optional

from PySide6 import QtCore
from playwright.async_api import async_playwright

from .models import ListingRecord, ScrapeConfig, ScrapeStats
from .parser import extract_listing_cards, parse_detail_page, summary_to_record
from .storage import InMemoryStorage
from .utils import DEFAULT_TIMEOUT, random_delay_seconds


class ScraperWorker(QtCore.QThread):
    log_message = QtCore.Signal(str)
    progress = QtCore.Signal(int, int, int, int)
    row_ready = QtCore.Signal(dict)
    finished = QtCore.Signal()

    def __init__(self, config: ScrapeConfig, storage: InMemoryStorage, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent)
        self.config = config
        self.storage = storage
        self._stop = False
        self.stats = ScrapeStats()

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
        finally:
            loop.close()

    async def _run(self) -> None:
        self.stats = ScrapeStats()
        try:
            async with async_playwright() as p:
                browser = await self._create_browser(p)
                page = await browser.new_page()
                await page.goto(self.config.listing_url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
                await page.wait_for_timeout(1500)

                for page_no in range(1, self.config.max_pages + 1):
                    if self._stop:
                        break
                    await self._scrape_listing_page(page, page_no)

                    next_selector = "a[rel='next'], a.next-prev"
                    has_next = await page.locator(next_selector).count() > 0
                    if page_no < self.config.max_pages and has_next:
                        try:
                            await page.locator(next_selector).first.click()
                            await page.wait_for_load_state("domcontentloaded")
                            await page.wait_for_timeout(1200)
                        except Exception as exc:
                            self._emit_log(f"Sonraki sayfaya geçerken hata: {exc}")
                            break
                    else:
                        break

                await browser.close()
        except Exception as exc:  # pylint: disable=broad-except
            tb = traceback.format_exc()
            self._emit_log(f"Kritik hata: {exc}\n{tb}")
        finally:
            self.finished.emit()

    def stop(self) -> None:
        self._stop = True

    async def _scrape_listing_page(self, page, page_index: int) -> None:
        summaries = await extract_listing_cards(page)
        self.stats.total_found += len(summaries)
        self.stats.remaining = self.stats.total_found - self.stats.processed
        self._emit_progress()
        for summary in summaries:
            if self._stop:
                break
            record = await self._process_summary(page, summary)
            if record and self.storage.add_record(record):
                self.stats.processed += 1
                self.stats.remaining = max(self.stats.total_found - self.stats.processed, 0)
                self.row_ready.emit(record.as_row())
            else:
                self.stats.failed += 1
            self._emit_progress()
            delay = random_delay_seconds(self.config.min_delay, self.config.max_delay)
            await page.wait_for_timeout(int(delay * 1000))
        self._emit_log(f"Sayfa {page_index} tamamlandı ({len(summaries)} ilan).")

    async def _process_summary(self, page, summary: dict) -> Optional[ListingRecord]:
        try:
            if self.config.fetch_details and summary.get("link"):
                await page.goto(summary["link"], wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
                await page.wait_for_timeout(900)
                record = await parse_detail_page(page, summary)
                if self.config.only_with_contact and not record.telefon:
                    return None
                return record
            record = await summary_to_record(summary)
            if self.config.only_with_contact:
                return None
            return record
        except Exception as exc:  # pylint: disable=broad-except
            self._emit_log(f"İlan işlenirken hata: {exc}")
            return None

    async def _create_browser(self, playwright):
        chromium = playwright.chromium
        if self.config.remote_debugging_url:
            return await chromium.connect_over_cdp(self.config.remote_debugging_url)
        return await chromium.launch_persistent_context(
            user_data_dir=str(self.config.user_data_dir),
            headless=False,
            channel="chrome",
        )

    def _emit_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.stats.log_lines.append(full_message)
        self.log_message.emit(full_message)

    def _emit_progress(self) -> None:
        self.progress.emit(*self.stats.as_progress_tuple())
