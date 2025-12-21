"""Entry point for the İlân Toplayıcı desktop app."""
from __future__ import annotations

import os
import sys

import pandas as pd
from PySide6 import QtCore, QtWidgets

from .exporter import export_csv, export_excel, export_json
from .models import ScrapeConfig
from .scraper import ScraperWorker
from .storage import InMemoryStorage
from .ui_main import PandasModel, UiMainWindow
from .utils import Paths, setup_logger


class AppController(QtCore.QObject):
    def __init__(self, window: UiMainWindow, paths: Paths) -> None:
        super().__init__()
        self.window = window
        self.paths = paths
        self.storage = InMemoryStorage()
        self.model = PandasModel(self.storage.dataframe)
        self.window.set_model(self.model)
        self.scraper: ScraperWorker | None = None
        self.logger = setup_logger()

        self.window.start_requested.connect(self.start_scraping)
        self.window.stop_requested.connect(self.stop_scraping)
        self.window.export_requested.connect(self.export_data)

    def start_scraping(self, config: ScrapeConfig) -> None:
        if self.scraper and self.scraper.isRunning():
            return
        config.user_data_dir = self.paths.profile_dir
        config.remote_debugging_url = os.environ.get("REMOTE_DEBUG_URL")
        self.window.toggle_run_state(True)
        self.storage.reset()
        self.model.update(self.storage.dataframe)
        self.scraper = ScraperWorker(config, self.storage)
        self.scraper.log_message.connect(self.window.append_log)
        self.scraper.progress.connect(self.window.update_stats)
        self.scraper.row_ready.connect(self._on_row_ready)
        self.scraper.finished.connect(self._on_finished)
        self.scraper.start()
        self.window.append_log("Tarama başladı. Lütfen açık olan tarayıcı oturumunuzun kullanıldığından emin olun.")

    def stop_scraping(self) -> None:
        if self.scraper:
            self.scraper.stop()
            self.window.append_log("Durdurma talebi gönderildi.")

    def _on_row_ready(self, row: dict) -> None:
        df = self.storage.dataframe
        self.model.update(df)
        self.window.table_view.resizeColumnsToContents()

    def _on_finished(self) -> None:
        self.window.toggle_run_state(False)
        self.window.append_log("Tarama tamamlandı.")

    def export_data(self, fmt: str) -> None:
        df = self.storage.dataframe
        try:
            if fmt == "excel":
                path = export_excel(df, self.paths.export_dir / "ilanlar.xlsx")
            elif fmt == "csv":
                path = export_csv(df, self.paths.export_dir / "ilanlar.csv")
            else:
                path = export_json(df, self.paths.export_dir / "ilanlar.json")
            self.window.append_log(f"Dışa aktarıldı: {path}")
        except Exception as exc:  # pylint: disable=broad-except
            QtWidgets.QMessageBox.warning(self.window, "Export Hatası", str(exc))


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    paths = Paths.default()
    window = UiMainWindow()
    controller = AppController(window, paths)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
