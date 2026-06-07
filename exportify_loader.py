"""Load and normalize Exportify (exportify.net) playlist CSV exports."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from config import EXPORTIFY_PLAYLISTS_DIR
from data_processing import (
    calculate_release_year,
    convert_duration_ms_to_min,
    split_artist_names,
    _parse_genres,
)

EXPORTIFY_COLUMNS = {
    "track_uri": "Track URI",
    "track_name": "Track Name",
    "album": "Album Name",
    "artist_names": "Artist Name(s)",
    "release_date": "Release Date",
    "duration_ms": "Duration (ms)",
    "popularity": "Popularity",
    "explicit": "Explicit",
    "genres": "Genres",
    "added_at": "Added At",
    "record_label": "Record Label",
}

AUDIO_FEATURE_COLUMNS = [
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
]

EXPORTIFY_AUDIO_MAP = {
    "danceability": "Danceability",
    "energy": "Energy",
    "key": "Key",
    "loudness": "Loudness",
    "mode": "Mode",
    "speechiness": "Speechiness",
    "acousticness": "Acousticness",
    "instrumentalness": "Instrumentalness",
    "liveness": "Liveness",
    "valence": "Valence",
    "tempo": "Tempo",
    "time_signature": "Time Signature",
}


def parse_track_id_from_uri(uri: str | None) -> str:
    if not uri or (isinstance(uri, float) and pd.isna(uri)):
        return ""
    s = str(uri).strip()
    if s.startswith("spotify:track:"):
        return s.split(":")[-1]
    return s


def is_exportify_dataframe(df: pd.DataFrame) -> bool:
    return "Track URI" in df.columns or "Track Name" in df.columns


def playlist_name_from_path(path: Path) -> str:
    stem = path.stem.strip()
    if not stem or stem == ".":
        return "Untitled playlist"
    return stem.replace("_", " ")


def playlist_slug_from_path(path: Path) -> str:
    stem = path.stem.strip() or "untitled"
    slug = re.sub(r"[^\w\-]+", "_", stem, flags=re.UNICODE).strip("_").lower()
    return slug or "playlist"


def normalize_exportify_dataframe(
    df: pd.DataFrame,
    playlist_name: str = "",
    source: str = "exportify",
) -> pd.DataFrame:
    """Map Exportify CSV rows to the app's track schema."""
    if df.empty:
        return pd.DataFrame()

    if not is_exportify_dataframe(df):
        return df

    rows: list[dict[str, Any]] = []
    for i, item in enumerate(df.to_dict("records")):
        row = _exportify_row_to_track(item, playlist_name, source, i)
        if row:
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _exportify_row_to_track(
    item: dict,
    playlist_name: str,
    source: str,
    position: int,
) -> dict[str, Any] | None:
    uri = item.get(EXPORTIFY_COLUMNS["track_uri"], "")
    track_id = parse_track_id_from_uri(uri)
    track_name = str(item.get(EXPORTIFY_COLUMNS["track_name"], "") or "").strip()
    if not track_name and not track_id:
        return None

    artist_field = item.get(EXPORTIFY_COLUMNS["artist_names"], "")
    names = split_artist_names(artist_field)
    artist_name = ", ".join(names) if names else str(artist_field or "").strip()
    primary_artist = names[0] if names else artist_name

    release_date = item.get(EXPORTIFY_COLUMNS["release_date"], "")
    genres_raw = item.get(EXPORTIFY_COLUMNS["genres"], "")
    genres = _parse_genres(genres_raw)
    genres_str = ", ".join(genres) if genres else str(genres_raw or "").strip()

    pop = item.get(EXPORTIFY_COLUMNS["popularity"])
    try:
        popularity = float(pop) if pop is not None and str(pop).strip() != "" else None
    except (TypeError, ValueError):
        popularity = None

    dur = item.get(EXPORTIFY_COLUMNS["duration_ms"])
    try:
        duration_ms = int(float(dur)) if dur is not None and str(dur).strip() != "" else None
    except (TypeError, ValueError):
        duration_ms = None

    explicit_raw = item.get(EXPORTIFY_COLUMNS["explicit"], False)
    if isinstance(explicit_raw, str):
        explicit = explicit_raw.strip().lower() in ("true", "1", "yes")
    else:
        explicit = bool(explicit_raw)

    row: dict[str, Any] = {
        "track_id": track_id,
        "track_name": track_name,
        "artist_name": artist_name,
        "primary_artist": primary_artist,
        "album": str(item.get(EXPORTIFY_COLUMNS["album"], "") or ""),
        "popularity": popularity,
        "release_date": str(release_date or ""),
        "release_year": calculate_release_year(release_date),
        "explicit": explicit,
        "duration_ms": duration_ms,
        "duration_min": convert_duration_ms_to_min(duration_ms),
        "external_url": f"https://open.spotify.com/track/{track_id}" if track_id else "",
        "source": source,
        "time_range": None,
        "rank": position + 1,
        "position": position,
        "genres": genres,
        "genres_str": genres_str,
        "added_at": item.get(EXPORTIFY_COLUMNS["added_at"], ""),
        "record_label": item.get(EXPORTIFY_COLUMNS["record_label"], ""),
        "playlist_name": playlist_name,
    }
    for col, exportify_col in EXPORTIFY_AUDIO_MAP.items():
        val = item.get(exportify_col)
        if val is not None and str(val).strip() != "":
            try:
                row[col] = float(val)
            except (TypeError, ValueError):
                row[col] = None
        else:
            row[col] = None
    return row


def _row_quality_score(row: dict) -> float:
    score = 0.0
    if row.get("genres_str"):
        score += 10.0
    pop = row.get("popularity")
    if pop is not None and not (isinstance(pop, float) and pd.isna(pop)):
        score += float(pop) / 10.0
    if row.get("danceability") is not None:
        score += 2.0
    return score


def build_enrichment_master(*frames: pd.DataFrame) -> pd.DataFrame:
    """Dedupe tracks by track_id; prefer rows with genres and higher popularity."""
    combined: list[dict] = []
    for df in frames:
        if df is None or df.empty:
            continue
        for _, r in df.iterrows():
            combined.append(r.to_dict())
    if not combined:
        return pd.DataFrame()

    by_id: dict[str, dict] = {}
    for row in combined:
        tid = str(row.get("track_id", "") or "").strip()
        key = tid if tid else f"{row.get('track_name', '')}|{row.get('artist_name', '')}".lower()
        if not key:
            continue
        existing = by_id.get(key)
        if existing is None or _row_quality_score(row) > _row_quality_score(existing):
            by_id[key] = row
    return pd.DataFrame(by_id.values())


def merge_api_with_exportify(api_df: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    """Fill missing API fields from Exportify master on track_id."""
    if api_df.empty:
        return api_df
    if master.empty:
        return api_df

    out = api_df.copy()
    if "track_id" not in out.columns:
        return out

    master_idx = master.drop_duplicates("track_id", keep="first").set_index("track_id")
    fill_cols = [
        "popularity",
        "genres",
        "genres_str",
        "genre_bucket",
        "region_tag",
        "scene_tag",
        "record_label",
        *AUDIO_FEATURE_COLUMNS,
    ]
    for col in fill_cols:
        if col not in master_idx.columns:
            continue
        if col not in out.columns:
            out[col] = None
        for idx, row in out.iterrows():
            tid = str(row.get("track_id", "") or "")
            if not tid or tid not in master_idx.index:
                continue
            cur = row.get(col)
            if cur is not None and not (isinstance(cur, float) and pd.isna(cur)) and cur != "":
                if col not in ("genres",) or (isinstance(cur, list) and cur):
                    continue
            new_val = master_idx.loc[tid, col]
            if new_val is not None and not (isinstance(new_val, float) and pd.isna(new_val)):
                out.at[idx, col] = new_val
    return out


def load_playlist_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    name = playlist_name_from_path(path)
    return normalize_exportify_dataframe(df, playlist_name=name)


def load_all_playlists(directory: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load every *.csv in spotify_playlists/ except aggregate library files handled separately."""
    root = directory or EXPORTIFY_PLAYLISTS_DIR
    if not root.exists():
        return {}

    skip_stems = {"full_library", "liked_songs"}
    result: dict[str, pd.DataFrame] = {}
    for path in sorted(root.glob("*.csv")):
        if path.stem.lower() in skip_stems:
            continue
        if not path.stem.strip() or path.stem == ".":
            continue
        try:
            df = load_playlist_csv(path)
        except Exception:
            continue
        if df.empty:
            continue
        slug = playlist_slug_from_path(path)
        pid = f"exportify_{slug}"
        df = df.copy()
        df["playlist_id"] = pid
        df["playlist_name"] = playlist_name_from_path(path)
        result[pid] = df
    return result


def load_special_csv(filename: str, directory: Path | None = None) -> pd.DataFrame:
    root = directory or EXPORTIFY_PLAYLISTS_DIR
    path = root / filename
    if not path.exists():
        return pd.DataFrame()
    return load_playlist_csv(path)


def build_playlists_metadata(playlist_tracks: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for pid, df in playlist_tracks.items():
        if df.empty:
            continue
        pname = df["playlist_name"].iloc[0] if "playlist_name" in df.columns else pid
        rows.append(
            {
                "playlist_id": pid,
                "playlist_name": pname,
                "track_count": len(df),
                "owner": "exportify",
                "public": None,
                "description": "Loaded from Exportify export",
            }
        )
    return pd.DataFrame(rows)


def summarize_audio_profile(df: pd.DataFrame) -> dict[str, float | int]:
    """Median audio features when Exportify columns are present."""
    if df.empty:
        return {}
    cols = ["tempo", "energy", "danceability", "valence"]
    present = [c for c in cols if c in df.columns]
    if not present:
        return {}
    numeric = df[present].apply(pd.to_numeric, errors="coerce")
    out: dict[str, float | int] = {"track_count": len(df)}
    for c in present:
        med = numeric[c].median()
        if pd.notna(med):
            out[f"median_{c}"] = round(float(med), 2)
    return out


def load_exportify_bundle(directory: Path | None = None) -> dict[str, Any]:
    """
    Load Full_Library, Liked_Songs, and all playlist CSVs.
    Returns dict with keys: exportify_master, saved_tracks, playlist_tracks, playlists, stats.
    """
    root = directory or EXPORTIFY_PLAYLISTS_DIR
    full_lib = load_special_csv("Full_Library.csv", root)
    liked = load_special_csv("Liked_Songs.csv", root)
    playlist_tracks = load_all_playlists(root)

    # Include library aggregates in master only (not as scored playlists)
    master = build_enrichment_master(full_lib, liked, *playlist_tracks.values())

    saved = liked.copy() if not liked.empty else full_lib.copy()
    if not saved.empty:
        saved = saved.drop_duplicates(subset=["track_id"], keep="first") if "track_id" in saved.columns else saved

    playlists = build_playlists_metadata(playlist_tracks)

    return {
        "exportify_master": master,
        "saved_tracks": saved,
        "playlist_tracks": playlist_tracks,
        "playlists": playlists,
        "stats": {
            "master_tracks": len(master),
            "playlists": len(playlist_tracks),
            "liked_tracks": len(liked),
            "library_tracks": len(full_lib),
        },
    }


@lru_cache(maxsize=2)
def cached_load_exportify_bundle(directory_str: str) -> dict[str, Any]:
    """In-process cache for Exportify bundle (Streamlit-free)."""
    return load_exportify_bundle(Path(directory_str))


def clear_exportify_bundle_cache() -> None:
    cached_load_exportify_bundle.cache_clear()


def get_exportify_bundle(force_reload: bool = False) -> dict[str, Any]:
    """Return Exportify bundle from cache."""
    if force_reload:
        clear_exportify_bundle_cache()
    return cached_load_exportify_bundle(str(EXPORTIFY_PLAYLISTS_DIR))
