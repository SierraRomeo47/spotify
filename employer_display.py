"""Employer-facing column allowlists and denylist for portfolio tables."""

from __future__ import annotations

from typing import Any

import pandas as pd

EMPLOYER_DROP_COLUMNS = frozenset(
    {
        "track_id",
        "artist_id",
        "album_id",
        "playlist_id",
        "uri",
        "track_uri",
        "artist_uri",
        "album_uri",
        "duration_ms",
        "time_range",
        "is_pre_long_term",
        "is_pre_long_term_artist",
        "editorial_note",
        "_key",
        "terms_present",
        "listen_velocity",
        "velocity_score",
    }
)

LONG_TERM_TRACK_PREFERRED = [
    "rank",
    "track_name",
    "artist_name",
    "genre_bucket",
    "region_tag",
    "scene_tag",
    "release_year",
    "popularity",
    "duration_min",
]

SEQUENCE_TRACK_COLUMNS = [
    "sequence_order",
    "role",
    "track",
    "artist",
    "reason_for_placement",
]


def long_term_track_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in LONG_TERM_TRACK_PREFERRED if c in df.columns]


def sequence_track_columns() -> list[str]:
    return list(SEQUENCE_TRACK_COLUMNS)


def filter_df_columns(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if columns:
        use = [c for c in columns if c in df.columns]
        return df[use] if use else df
    keep = [c for c in df.columns if c not in EMPLOYER_DROP_COLUMNS]
    return df[keep]


def filter_records(
    records: list[dict[str, Any]],
    columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    if not records:
        return []
    if columns:
        return [{k: row.get(k) for k in columns if k in row} for row in records]
    return [{k: v for k, v in row.items() if k not in EMPLOYER_DROP_COLUMNS} for row in records]
