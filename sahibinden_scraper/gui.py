"""Tkinter based GUI for the Sahibinden scraper."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import BooleanVar, IntVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from typing import Optional

import pandas as pd

from .config import ProxySettings, ScraperConfig, SearchFilters
from .scraper import SahibindenScraper, ScraperError
from .utils import setup_logging

LOGGER = logging.getLogger(__name__)


class ScraperGUI:
    """Encapsulates the Tkinter widgets and interactions."""

    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Sahibinden.com Emlak Çekici")
        self.root.geometry("950x600")

        self.config = ScraperConfig()
        setup_logging(self.config.log_file)

        self.scraper = SahibindenScraper(self.config)
        self.listings_df: Optional[pd.DataFrame] = None

        self._create_variables()
        self._build_layout()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _create_variables(self) -> None:
        self.city = StringVar()
        self.district = StringVar()
        self.listing_type = StringVar(value="satilik")
        self.property_type = StringVar()
        self.price_min = StringVar()
        self.price_max = StringVar()
        self.room_count = StringVar()
        self.area_min = StringVar()
        self.area_max = StringVar()
        self.exclude_keywords = StringVar()
        self.exclude_urgent = BooleanVar(value=False)
        self.include_photos = BooleanVar(value=False)
        self.max_listings = IntVar(value=self.config.max_listings)
        self.output_dir = StringVar(value=str(self.config.output_directory))
        self.http_proxy = StringVar(value=self.scraper.proxies.http or "")
        self.https_proxy = StringVar(value=self.scraper.proxies.https or "")
        self.use_selenium = BooleanVar(value=self.config.use_selenium)

    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        filters_frame = ttk.LabelFrame(main_frame, text="Filtreler", padding=10)
        filters_frame.pack(fill="x", expand=False)

        self._add_entry(filters_frame, "Şehir", self.city, 0, 0)
        self._add_entry(filters_frame, "İlçe", self.district, 0, 1)

        ttk.Label(filters_frame, text="İlan Tipi").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(
            filters_frame,
            textvariable=self.listing_type,
            values=("satilik", "kiralik"),
            state="readonly",
            width=22,
        ).grid(row=1, column=1, sticky="ew")

        ttk.Label(filters_frame, text="Emlak Türü").grid(row=1, column=2, sticky="w")
        ttk.Combobox(
            filters_frame,
            textvariable=self.property_type,
            values=("daire", "villa", "arsa", "is yeri", ""),
            width=22,
        ).grid(row=1, column=3, sticky="ew")

        self._add_entry(filters_frame, "Min Fiyat", self.price_min, 2, 0)
        self._add_entry(filters_frame, "Max Fiyat", self.price_max, 2, 1)
        self._add_entry(filters_frame, "Oda Sayısı", self.room_count, 2, 2)
        self._add_entry(filters_frame, "Min m²", self.area_min, 2, 3)
        self._add_entry(filters_frame, "Max m²", self.area_max, 3, 0)

        ttk.Checkbutton(
            filters_frame,
            text="Acil ilanları hariç tut",
            variable=self.exclude_urgent,
        ).grid(row=3, column=1, sticky="w")

        ttk.Checkbutton(
            filters_frame,
            text="Sadece fotoğraflı ilanlar",
            variable=self.include_photos,
        ).grid(row=3, column=2, sticky="w")

        self._add_entry(filters_frame, "Hariç tutulacak kelimeler", self.exclude_keywords, 4, 0, columnspan=4)

        settings_frame = ttk.LabelFrame(main_frame, text="Ayarlar", padding=10)
        settings_frame.pack(fill="x", expand=False, pady=(10, 0))
        settings_frame.columnconfigure((1, 3), weight=1)

        self._add_entry(
            settings_frame,
            "İlan limiti",
            self.max_listings,
            0,
            0,
        )
        ttk.Button(settings_frame, text="Çıktı klasörü seç", command=self._choose_directory).grid(
            row=0, column=1, padx=5
        )
        ttk.Label(settings_frame, textvariable=self.output_dir).grid(row=0, column=2, sticky="w")

        ttk.Label(settings_frame, text="HTTP Proxy").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(settings_frame, textvariable=self.http_proxy, width=30).grid(
            row=1, column=1, sticky="ew", padx=5
        )
        ttk.Label(settings_frame, text="HTTPS Proxy").grid(row=1, column=2, sticky="w", pady=5)
        ttk.Entry(settings_frame, textvariable=self.https_proxy, width=30).grid(
            row=1, column=3, sticky="ew", padx=5
        )

        ttk.Checkbutton(
            settings_frame,
            text="Headless Selenium kullan",
            variable=self.use_selenium,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        controls_frame = ttk.Frame(main_frame, padding=(0, 10))
        controls_frame.pack(fill="x", expand=False)

        ttk.Button(controls_frame, text="İlanları Ara", command=self._start_scraping).pack(
            side="left", padx=5
        )
        ttk.Button(controls_frame, text="Excel'e Aktar", command=self._export_results).pack(
            side="left", padx=5
        )

        self.progress = ttk.Progressbar(controls_frame, mode="determinate")
        self.progress.pack(fill="x", expand=True, padx=5)

        self.status_label = ttk.Label(controls_frame, text="Hazır")
        self.status_label.pack(side="left", padx=5)

        columns = (
            "listing_id",
            "title",
            "price",
            "location",
            "area",
            "room_count",
            "publish_date",
            "seller",
        )
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120 if col != "title" else 260)
        self.tree.pack(fill="both", expand=True)

    def _add_entry(
        self,
        parent: ttk.Frame,
        label: str,
        variable,
        row: int,
        column: int,
        columnspan: int = 1,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variable, width=22)
        entry.grid(row=row, column=column + 1, sticky="ew", padx=5, pady=5, columnspan=columnspan)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _choose_directory(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
            self.scraper.config.output_directory = Path(directory)

    def _start_scraping(self) -> None:
        try:
            limit = int(self.max_listings.get())
            self.config.max_listings = limit
        except ValueError:
            messagebox.showerror("Hata", "İlan limiti sayısal olmalıdır")
            return

        self.progress.configure(maximum=self.config.max_listings, value=0)
        self.status_label.config(text="İlanlar çekiliyor...")

        self.scraper.config.use_selenium = self.use_selenium.get()
        self.scraper.proxies = ProxySettings(
            http=self.http_proxy.get() or None,
            https=self.https_proxy.get() or None,
        )

        thread = threading.Thread(target=self._scrape_in_background, daemon=True)
        thread.start()

    def _scrape_in_background(self) -> None:
        try:
            filters = self._collect_filters()
            df = self.scraper.fetch_listings(filters, progress_callback=self._update_progress)
        except ScraperError as exc:
            LOGGER.exception("Scraper error")
            self._update_status(f"Hata: {exc}")
            self._show_error(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Beklenmeyen hata")
            self._update_status("Beklenmeyen bir hata oluştu")
            self._show_error(str(exc))
            return

        self.root.after(0, lambda: self._handle_results(df))

    def _collect_filters(self) -> SearchFilters:
        exclude = [term.strip() for term in self.exclude_keywords.get().split(",") if term.strip()]
        filters = SearchFilters(
            city=self.city.get(),
            district=self.district.get(),
            listing_type=self.listing_type.get(),
            property_type=self.property_type.get(),
            price_min=self._safe_int(self.price_min.get()),
            price_max=self._safe_int(self.price_max.get()),
            room_count=self.room_count.get() or None,
            area_min=self._safe_int(self.area_min.get()),
            area_max=self._safe_int(self.area_max.get()),
            exclude_keywords=exclude,
            exclude_urgent=self.exclude_urgent.get(),
            include_photos=self.include_photos.get(),
        )
        return filters

    def _update_progress(self, current: int, total: Optional[int]) -> None:
        self.root.after(0, lambda: self._update_progress_ui(current, total))

    def _update_progress_ui(self, current: int, total: Optional[int]) -> None:
        self.progress.configure(value=current)
        if total:
            self.progress.configure(maximum=total)
        self.status_label.config(text=f"{current}/{total or '?'} ilan")

    def _populate_tree(self, df: pd.DataFrame) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        if df.empty:
            return
        for _, row in df.iterrows():
            values = (
                row.get("listing_id", ""),
                row.get("title", ""),
                row.get("price", ""),
                row.get("location", ""),
                row.get("area", ""),
                row.get("room_count", ""),
                row.get("publish_date", ""),
                row.get("seller", ""),
            )
            self.tree.insert("", "end", values=values)

    def _export_results(self) -> None:
        if self.listings_df is None or self.listings_df.empty:
            self._show_info("Önce ilanları arayın")
            return
        output_dir = Path(self.output_dir.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "sahibinden_listings.xlsx"
        path = self.scraper.export_listings(self.listings_df, str(output_file), to_excel=True)
        self._show_info(f"Dosya kaydedildi: {path}")

    def _safe_int(self, value: str) -> Optional[int]:
        try:
            return int(value) if value else None
        except ValueError:
            return None

    def _update_status(self, message: str) -> None:
        self.root.after(0, lambda: self.status_label.config(text=message))

    def _handle_results(self, df: pd.DataFrame) -> None:
        self.listings_df = df
        self._populate_tree(df)
        self.status_label.config(text=f"{len(df)} ilan bulundu")

    def _show_error(self, message: str) -> None:
        self.root.after(0, lambda: messagebox.showerror("Hata", message))

    def _show_info(self, message: str) -> None:
        self.root.after(0, lambda: messagebox.showinfo("Bilgi", message))


def launch_gui() -> None:
    root = Tk()
    app = ScraperGUI(root)
    root.mainloop()


__all__ = ["ScraperGUI", "launch_gui"]


if __name__ == "__main__":
    launch_gui()
