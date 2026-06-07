#!/usr/bin/env python3
"""Build static portfolio JSON for Vercel (run from project root)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import SITE_DATA_PATH
from portfolio_site_builder import write_portfolio_json


def main() -> int:
    path = write_portfolio_json(SITE_DATA_PATH)
    size_kb = path.stat().st_size / 1024
    print(f"Wrote {path} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
