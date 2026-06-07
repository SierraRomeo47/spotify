"""Load Spotify privacy export JSON from my_spotify_data/Spotify Account Data/."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from config import SPOTIFY_ACCOUNT_DATA_DIR
from data_processing import (
    calculate_release_year,
    classify_genres,
    classify_region,
    normalize_recently_played,
    normalize_tracks,
)
from exportify_loader import (
    build_enrichment_master,
    build_playlists_metadata,
    parse_track_id_from_uri,
)
from data_processing import _norm_name


def account_data_available(directory: Path | None = None) -> bool:
    root = directory or SPOTIFY_ACCOUNT_DATA_DIR
    if not root.exists():
        return False
    if any(root.glob("StreamingHistory_music_*.json")):
        return True
    if (root / "YourLibrary.json").exists():
        return True
    return any(root.glob("Playlist*.json"))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", name.strip(), flags=re.UNICODE).strip("_").lower()
    return slug or "playlist"


def load_streaming_history(directory: Path | None = None) -> pd.DataFrame:
    """Merge StreamingHistory_music_*.json into one frame."""
    root = directory or SPOTIFY_ACCOUNT_DATA_DIR
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("StreamingHistory_music_*.json")):
        try:
            batch = _read_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(batch, list):
            continue
        for item in batch:
            end_time = item.get("endTime", "")
            played_at = _parse_end_time(end_time)
            rows.append(
                {
                    "track_name": item.get("trackName", ""),
                    "artist_name": item.get("artistName", ""),
                    "played_at": played_at,
                    "ms_played": int(item.get("msPlayed") or 0),
                    "source": "account_streaming",
                }
            )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["played_at"] = pd.to_datetime(df["played_at"], errors="coerce", utc=True)
    df = df.dropna(subset=["played_at"]).sort_values("played_at", ascending=False)
    return df.reset_index(drop=True)


def _parse_end_time(end_time: str) -> str:
    if not end_time:
        return ""
    try:
        dt = datetime.strptime(end_time.strip(), "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return end_time


def load_your_library(directory: Path | None = None) -> pd.DataFrame:
    root = directory or SPOTIFY_ACCOUNT_DATA_DIR
    path = root / "YourLibrary.json"
    if not path.exists():
        return pd.DataFrame()
    try:
        data = _read_json(path)
    except (json.JSONDecodeError, OSError):
        return pd.DataFrame()
    tracks = data.get("tracks") or []
    rows = []
    for i, item in enumerate(tracks):
        uri = item.get("uri", "")
        rows.append(
            {
                "track_id": parse_track_id_from_uri(uri),
                "track_name": item.get("track", ""),
                "artist_name": item.get("artist", ""),
                "album": item.get("album", ""),
                "track_uri": uri,
                "source": "account_library",
                "rank": i + 1,
            }
        )
    return normalize_tracks(rows, source="account", time_range=None)


def load_account_playlists(directory: Path | None = None) -> dict[str, pd.DataFrame]:
    root = directory or SPOTIFY_ACCOUNT_DATA_DIR
    result: dict[str, pd.DataFrame] = {}
    for path in sorted(root.glob("Playlist*.json")):
        try:
            data = _read_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        for pl in data.get("playlists") or []:
            name = pl.get("name") or "Untitled playlist"
            pid = f"account_{_slugify(name)}"
            rows = []
            for pos, item in enumerate(pl.get("items") or [], start=1):
                track = item.get("track") or {}
                uri = track.get("trackUri", "")
                rows.append(
                    {
                        "track_id": parse_track_id_from_uri(uri),
                        "track_name": track.get("trackName", ""),
                        "artist_name": track.get("artistName", ""),
                        "album": track.get("albumName", ""),
                        "playlist_id": pid,
                        "playlist_name": name,
                        "added_at": item.get("addedDate", ""),
                        "source": "account_playlist",
                        "rank": pos,
                    }
                )
            if rows:
                result[pid] = pd.DataFrame(rows)
    return result


def _build_uri_lookup(*frames: pd.DataFrame) -> dict[tuple[str, str], str]:
    lookup: dict[tuple[str, str], str] = {}
    for df in frames:
        if df is None or df.empty:
            continue
        for _, r in df.iterrows():
            tid = str(r.get("track_id", "") or "").strip()
            if not tid:
                continue
            key = (_norm_name(r.get("track_name", "")), _norm_name(r.get("artist_name", "")))
            if key[0]:
                lookup[key] = tid
    return lookup


def streaming_to_recent(
    streaming: pd.DataFrame,
    uri_lookup: dict[tuple[str, str], str] | None = None,
    limit: int | None = 500,
) -> pd.DataFrame:
    if streaming.empty:
        return pd.DataFrame()
    subset = streaming.head(limit) if limit else streaming
    rows = []
    for _, r in subset.iterrows():
        key = (_norm_name(r["track_name"]), _norm_name(r["artist_name"]))
        track_id = (uri_lookup or {}).get(key, "")
        rows.append(
            {
                "track_id": track_id,
                "track_name": r["track_name"],
                "artist_name": r["artist_name"],
                "played_at": r["played_at"].isoformat() if hasattr(r["played_at"], "isoformat") else r["played_at"],
                "ms_played": r.get("ms_played"),
                "source": "account_streaming",
            }
        )
    return normalize_recently_played(rows)


def derive_top_tracks_from_streaming(
    streaming: pd.DataFrame,
    uri_lookup: dict[tuple[str, str], str] | None = None,
    limit: int = 50,
) -> pd.DataFrame:
    if streaming.empty:
        return pd.DataFrame()
    df = streaming.copy()
    if df["played_at"].dt.tz is None:
        df["played_at"] = df["played_at"].dt.tz_localize(timezone.utc)
    max_date = df["played_at"].max()
    windows = {
        "short_term": max_date - timedelta(days=28),
        "medium_term": max_date - timedelta(days=180),
        "long_term": None,
    }
    all_rows: list[dict] = []
    for time_range, cutoff in windows.items():
        subset = df if cutoff is None else df[df["played_at"] >= cutoff]
        if subset.empty:
            continue
        agg = (
            subset.groupby(["track_name", "artist_name"], as_index=False)
            .agg(play_count=("ms_played", "count"), ms_played=("ms_played", "sum"))
            .sort_values(["play_count", "ms_played"], ascending=False)
            .head(limit)
        )
        for rank, row in enumerate(agg.to_dict("records"), start=1):
            key = (_norm_name(row["track_name"]), _norm_name(row["artist_name"]))
            all_rows.append(
                {
                    "track_id": (uri_lookup or {}).get(key, ""),
                    "track_name": row["track_name"],
                    "artist_name": row["artist_name"],
                    "time_range": time_range,
                    "rank": rank,
                    "play_count": row["play_count"],
                    "source": "account_streaming",
                }
            )
    return normalize_tracks(all_rows, source="account", time_range=None)


def derive_top_artists_from_streaming(streaming: pd.DataFrame, limit: int = 50) -> pd.DataFrame:
    if streaming.empty:
        return pd.DataFrame()
    df = streaming.copy()
    if df["played_at"].dt.tz is None:
        df["played_at"] = df["played_at"].dt.tz_localize(timezone.utc)
    max_date = df["played_at"].max()
    windows = {
        "short_term": max_date - timedelta(days=28),
        "medium_term": max_date - timedelta(days=180),
        "long_term": None,
    }
    rows: list[dict] = []
    for time_range, cutoff in windows.items():
        subset = df if cutoff is None else df[df["played_at"] >= cutoff]
        if subset.empty:
            continue
        agg = (
            subset.groupby("artist_name", as_index=False)
            .agg(play_count=("ms_played", "count"))
            .sort_values("play_count", ascending=False)
            .head(limit)
        )
        for rank, item in enumerate(agg.to_dict("records"), start=1):
            name = item["artist_name"]
            rows.append(
                {
                    "artist_name": name,
                    "artist_id": "",
                    "time_range": time_range,
                    "rank": rank,
                    "genres": [],
                    "genres_str": "",
                    "genre_bucket": classify_genres([]),
                    "region_tag": classify_region([], name),
                }
            )
    return pd.DataFrame(rows)


def load_spotify_account_bundle(directory: Path | None = None) -> dict[str, Any]:
    """
    Load privacy export bundle: streaming, library, playlists, derived top tracks/artists.
    """
    root = directory or SPOTIFY_ACCOUNT_DATA_DIR
    streaming = load_streaming_history(root)
    saved = load_your_library(root)
    playlist_tracks = load_account_playlists(root)
    uri_lookup = _build_uri_lookup(saved, *playlist_tracks.values())

    recent = streaming_to_recent(streaming, uri_lookup, limit=2000)
    tracks = derive_top_tracks_from_streaming(streaming, uri_lookup)
    artists = derive_top_artists_from_streaming(streaming)
    playlists = build_playlists_metadata(playlist_tracks)
    if not playlists.empty:
        playlists = playlists.copy()
        playlists["owner"] = "spotify_account"
        playlists["description"] = "Spotify privacy export"

    master_frames = [saved, recent, tracks, *playlist_tracks.values()]
    master = build_enrichment_master(*master_frames)

    return {
        "exportify_master": master,
        "saved_tracks": saved,
        "playlist_tracks": playlist_tracks,
        "playlists": playlists,
        "streaming_history": streaming,
        "recent": recent,
        "tracks": tracks,
        "artists": artists,
        "stats": {
            "master_tracks": len(master),
            "playlists": len(playlist_tracks),
            "liked_tracks": len(saved),
            "library_tracks": len(saved),
            "streaming_plays": len(streaming),
            "recent_plays": len(recent),
        },
    }


@lru_cache(maxsize=2)
def cached_load_account_bundle(directory_str: str) -> dict[str, Any]:
    return load_spotify_account_bundle(Path(directory_str))


def clear_account_bundle_cache() -> None:
    cached_load_account_bundle.cache_clear()


def get_spotify_account_bundle(force_reload: bool = False) -> dict[str, Any]:
    if force_reload:
        clear_account_bundle_cache()
    return cached_load_account_bundle(str(SPOTIFY_ACCOUNT_DATA_DIR))
