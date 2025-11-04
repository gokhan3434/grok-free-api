"""Utility helpers for exporting listing information."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_dataframe(df: pd.DataFrame, destination: Path, to_excel: bool = True) -> Path:
    """Write the dataframe to ``destination``.

    Parameters
    ----------
    df:
        DataFrame that should be exported. Duplicate rows are removed before
        writing to disk.
    destination:
        Directory or full path where the file should be created.
    to_excel:
        When ``True`` (default) the dataframe is exported as ``.xlsx`` using
        :mod:`openpyxl`. Otherwise a CSV file is produced.
    """

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    sanitized = df.drop_duplicates()
    if to_excel:
        if destination.suffix.lower() != ".xlsx":
            destination = destination.with_suffix(".xlsx")
        sanitized.to_excel(destination, index=False)
    else:
        if destination.suffix.lower() != ".csv":
            destination = destination.with_suffix(".csv")
        sanitized.to_csv(destination, index=False)

    return destination
