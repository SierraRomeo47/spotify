"""Export helpers."""

from pathlib import Path

import pandas as pd

from config import OUTPUTS_DIR


def ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def export_csv(df: pd.DataFrame, filename: str) -> Path:
    path = ensure_outputs_dir() / filename
    df.to_csv(path, index=False)
    return path


def export_markdown(content: str, filename: str = "editorial_summary.md") -> Path:
    path = ensure_outputs_dir() / filename
    path.write_text(content, encoding="utf-8")
    return path
