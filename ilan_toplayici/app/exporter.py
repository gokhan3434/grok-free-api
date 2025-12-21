"""Export helpers for saving scraped data."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def export_excel(df: pd.DataFrame, path: Path) -> Path:
    if df.empty:
        raise ValueError("Export verisi boş")
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
        sheet = writer.sheets[writer.sheet_names[0]]
        for col_cells in sheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col_cells)
            sheet.column_dimensions[col_cells[0].column_letter].width = max(12, max_len + 2)
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True)
    return path


def export_csv(df: pd.DataFrame, path: Path) -> Path:
    if df.empty:
        raise ValueError("Export verisi boş")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def export_json(df: pd.DataFrame, path: Path) -> Path:
    if df.empty:
        raise ValueError("Export verisi boş")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(path, orient="records", force_ascii=False, indent=2)
    return path
