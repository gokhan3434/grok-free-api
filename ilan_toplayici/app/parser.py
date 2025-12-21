"""Parsing helpers for sahibinden.com pages using Playwright."""
from __future__ import annotations

from typing import List

from playwright.async_api import Locator, Page

from .models import ListingRecord


async def extract_listing_cards(page: Page) -> List[dict]:
    """Collect listing card metadata from the current listing page."""
    cards: List[dict] = []
    candidate_selectors = [
        "div.searchResultsItem",
        "tr.searchResultsItem",
        "div[class*='classified']",
    ]
    locator: Locator | None = None
    for selector in candidate_selectors:
        loc = page.locator(selector)
        if await loc.count() > 0:
            locator = loc
            break
    if locator is None:
        return cards

    count = await locator.count()
    for idx in range(count):
        item = locator.nth(idx)
        link = await _safe_inner_attr(item, "a", "href")
        title = await _safe_inner_text(item, "a")
        price = await _safe_inner_text(item, "[class*='price']")
        location = await _safe_inner_text(item, "[class*='location']")
        ilan_no = await _safe_inner_text(item, "[data-id]")
        if link:
            cards.append(
                {
                    "link": link,
                    "baslik": title or "(Başlıksız)",
                    "fiyat": price,
                    "konum": location,
                    "ilan_no": ilan_no,
                }
            )
    return cards


async def parse_detail_page(page: Page, summary: dict) -> ListingRecord:
    """Extract detail fields with defensive selectors."""
    ilan_no = await _first_text(page, ["text=İlan No", "xpath=//li[contains(text(),'İlan No')]"])
    ilan_tarihi = await _first_text(
        page,
        [
            "text=İlan Tarihi",
            "xpath=//li[contains(text(),'İlan Tarihi')]",
            "css=div.classifiedInfo li:has-text('İlan Tarihi')",
        ],
    )
    metrekare = await _first_text(page, ["text=m²", "xpath=//li[contains(text(),'m²')]"])
    address = await _first_text(
        page,
        [
            "css=div.classifiedInfo li:has-text('Adres')",
            "css=div.address",
            "css=div[class*='location']",
        ],
    )
    seller_type = await _first_text(page, ["text=Emlak Ofisi", "text=Bireysel"])
    seller_name = await _first_text(page, ["css=div.classifiedUserContent h3", "css=div.userName"])
    message_available = "Var" if await _element_exists(page, "text=Mesaj Gönder") else "Yok"
    phone_number = await _first_text(page, ["css=button.phone", "css=a[href^='tel']"])
    profile_link = await _first_attr(page, ["css=div.classifiedUserContent a", "css=a.userLink"], "href")
    description = await _first_text(page, ["css=#classifiedDescription", "css=.classifiedDescription"])

    il = ilce = mahalle = None
    if address and "," in address:
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 1:
            il = parts[-1]
        if len(parts) >= 2:
            ilce = parts[-2]
        if len(parts) >= 3:
            mahalle = parts[-3]

    return ListingRecord(
        ilan_no=ilan_no or summary.get("ilan_no"),
        baslik=summary.get("baslik", "(Başlıksız)"),
        fiyat=summary.get("fiyat"),
        metrekare=metrekare,
        konum=summary.get("konum"),
        il=il,
        ilce=ilce,
        mahalle=mahalle,
        ilan_tarihi=ilan_tarihi,
        ilan_tipi=summary.get("ilan_tipi"),
        tur=summary.get("tur"),
        ilan_sahibi_tipi=seller_type,
        ilan_sahibi_adi=seller_name,
        telefon=phone_number,
        mesaj=message_available,
        link=summary.get("link", ""),
        aciklama=description,
        profil_link=profile_link,
    )


async def summary_to_record(summary: dict) -> ListingRecord:
    return ListingRecord(
        ilan_no=summary.get("ilan_no"),
        baslik=summary.get("baslik", "(Başlıksız)"),
        fiyat=summary.get("fiyat"),
        metrekare=None,
        konum=summary.get("konum"),
        il=None,
        ilce=None,
        mahalle=None,
        ilan_tarihi=None,
        ilan_tipi=summary.get("ilan_tipi"),
        tur=summary.get("tur"),
        ilan_sahibi_tipi=None,
        ilan_sahibi_adi=None,
        telefon=None,
        mesaj=None,
        link=summary.get("link", ""),
    )


async def _first_text(page: Page, selectors: list[str]) -> str | None:
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if await el.count() > 0:
                text = await el.inner_text()
                if text:
                    return text.strip()
        except Exception:
            continue
    return None


async def _first_attr(page: Page, selectors: list[str], attr: str) -> str | None:
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if await el.count() > 0:
                val = await el.get_attribute(attr)
                if val:
                    return val.strip()
        except Exception:
            continue
    return None


async def _element_exists(page: Page, selector: str) -> bool:
    try:
        return await page.locator(selector).count() > 0
    except Exception:
        return False


async def _safe_inner_text(locator: Locator, selector: str) -> str | None:
    try:
        target = locator.locator(selector)
        if await target.count() == 0:
            return None
        text = await target.first.inner_text()
        return text.strip()
    except Exception:
        return None


async def _safe_inner_attr(locator: Locator, selector: str, attr: str) -> str | None:
    try:
        target = locator.locator(selector)
        if await target.count() == 0:
            return None
        value = await target.first.get_attribute(attr)
        return value.strip() if value else None
    except Exception:
        return None
