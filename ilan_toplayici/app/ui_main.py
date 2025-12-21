"""Main window UI built with PySide6."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets

from .models import ListingRecord, ScrapeConfig


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df: pd.DataFrame, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._df = df.copy()

    def update(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self._df.index)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self._df.columns)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return None
        value = self._df.iat[index.row(), index.column()]
        return str(value) if value is not None else ""

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


class UiMainWindow(QtWidgets.QMainWindow):
    start_requested = QtCore.Signal(ScrapeConfig)
    stop_requested = QtCore.Signal()
    export_requested = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("İlan Toplayıcı")
        self.resize(1200, 720)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        content_layout = QtWidgets.QHBoxLayout()

        # Left panel
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("Sahibinden listeleme URL'si")
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems(["(Belirtme)", "Satılık", "Kiralık", "Ev", "Arsa"])
        self.max_pages = QtWidgets.QSpinBox()
        self.max_pages.setRange(1, 200)
        self.max_pages.setValue(5)
        self.delay_min = QtWidgets.QDoubleSpinBox()
        self.delay_min.setRange(0, 30)
        self.delay_min.setDecimals(1)
        self.delay_min.setValue(1.0)
        self.delay_max = QtWidgets.QDoubleSpinBox()
        self.delay_max.setRange(0, 60)
        self.delay_max.setDecimals(1)
        self.delay_max.setValue(3.0)
        self.fetch_details = QtWidgets.QCheckBox("Detay sayfasına gir")
        self.fetch_details.setChecked(True)
        self.only_contact = QtWidgets.QCheckBox("Sadece iletişim bilgisi olanlar")
        self.start_btn = QtWidgets.QPushButton("Başlat")
        self.stop_btn = QtWidgets.QPushButton("Durdur")
        self.stop_btn.setEnabled(False)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Listeleme URL", self.url_edit)
        form_layout.addRow("Kategori", self.category_combo)
        form_layout.addRow("Max sayfa", self.max_pages)
        form_layout.addRow("Gecikme (sn) min", self.delay_min)
        form_layout.addRow("Gecikme (sn) max", self.delay_max)
        form_layout.addRow(self.fetch_details)
        form_layout.addRow(self.only_contact)
        form_layout.addRow(self.start_btn)
        form_layout.addRow(self.stop_btn)

        left_panel = QtWidgets.QGroupBox("Ayarlar")
        left_panel.setLayout(form_layout)

        # Center table
        self.table_view = QtWidgets.QTableView()
        self.table_view.setSortingEnabled(True)

        # Bottom log
        log_container = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout()
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        stats_layout = QtWidgets.QHBoxLayout()
        self.total_label = QtWidgets.QLabel("Toplam: 0")
        self.processed_label = QtWidgets.QLabel("İşlenen: 0")
        self.failed_label = QtWidgets.QLabel("Hatalı: 0")
        self.remaining_label = QtWidgets.QLabel("Kalan: 0")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.processed_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addWidget(self.remaining_label)
        stats_layout.addStretch()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        export_buttons = QtWidgets.QHBoxLayout()
        self.export_excel_btn = QtWidgets.QPushButton("Excel")
        self.export_csv_btn = QtWidgets.QPushButton("CSV")
        self.export_json_btn = QtWidgets.QPushButton("JSON")
        export_buttons.addWidget(self.export_excel_btn)
        export_buttons.addWidget(self.export_csv_btn)
        export_buttons.addWidget(self.export_json_btn)
        export_buttons.addStretch()

        log_layout.addWidget(self.log_text)
        log_layout.addLayout(stats_layout)
        log_layout.addWidget(self.progress_bar)
        log_layout.addLayout(export_buttons)
        log_container.setLayout(log_layout)

        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(self.table_view, 3)

        layout.addLayout(content_layout)
        layout.addWidget(log_container)
        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(lambda: self.stop_requested.emit())
        self.export_excel_btn.clicked.connect(lambda: self.export_requested.emit("excel"))
        self.export_csv_btn.clicked.connect(lambda: self.export_requested.emit("csv"))
        self.export_json_btn.clicked.connect(lambda: self.export_requested.emit("json"))

    def set_model(self, model: PandasModel) -> None:
        self.table_view.setModel(model)

    def _on_start(self) -> None:
        if not self.url_edit.text():
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Listeleme URL'si zorunludur")
            return
        config = ScrapeConfig(
            listing_url=self.url_edit.text().strip(),
            max_pages=int(self.max_pages.value()),
            min_delay=float(self.delay_min.value()),
            max_delay=float(self.delay_max.value()),
            fetch_details=self.fetch_details.isChecked(),
            only_with_contact=self.only_contact.isChecked(),
            category_hint=self.category_combo.currentText() if self.category_combo.currentIndex() > 0 else None,
        )
        self.start_requested.emit(config)

    # UI update helpers
    def append_log(self, message: str) -> None:
        self.log_text.appendPlainText(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def update_stats(self, total: int, processed: int, failed: int, remaining: int) -> None:
        self.total_label.setText(f"Toplam: {total}")
        self.processed_label.setText(f"İşlenen: {processed}")
        self.failed_label.setText(f"Hatalı: {failed}")
        self.remaining_label.setText(f"Kalan: {remaining}")
        total_items = max(total, processed + failed + remaining)
        percent = int((processed / total_items) * 100) if total_items else 0
        self.progress_bar.setValue(percent)

    def toggle_run_state(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def populate_table(self, df: pd.DataFrame, model: PandasModel) -> None:
        model.update(df)
        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()
