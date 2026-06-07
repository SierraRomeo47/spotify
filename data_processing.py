"""Data normalization, classification, and loading."""

from __future__ import annotations

import ast
import re
from datetime import datetime
from typing import Any

import pandas as pd

from config import (
    HIP_HOP_KEYWORDS,
    INDIA_KEYWORDS,
    INTERNATIONAL_BUCKETS,
    LANGUAGE_KEYWORDS,
    SCENE_KEYWORDS,
    TIME_RANGES,
)


def _norm_name(name: str) -> str:
    return str(name).strip().lower() if pd.notna(name) else ""


_TAG_WORD_FIXES = {
    "Uk": "UK",
    "Us": "US",
    "Edm": "EDM",
    "R&b": "R&B",
    "Hip-hop": "Hip-Hop",
    "Pop-rap": "Pop-Rap",
    "India-global": "India-Global",
    "Punjabi": "Punjabi",
}


def format_tag_label(value: str | None) -> str:
    """Title-case editorial tags; use middle dots instead of slashes for readability."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("/", " · ")
    parts = [p.strip() for p in text.split(" · ") if p.strip()]
    out: list[str] = []
    for part in parts:
        titled = part.title()
        for old, new in _TAG_WORD_FIXES.items():
            titled = titled.replace(old, new)
        out.append(titled)
    return " · ".join(out)


# Split Spotify collab strings: "A, B, C" / "A & B" / "A feat. B"
_ARTIST_SPLIT_RE = re.compile(
    r"\s*;\s*|\s*,\s*|\s+&\s+|\s+x\s+|\s+feat\.?\s+|\s+ft\.?\s+|\s+with\s+",
    flags=re.IGNORECASE,
)


def split_artist_names(artist_field: str | None) -> list[str]:
    """Return individual artist names from a combined artist string."""
    if artist_field is None or (isinstance(artist_field, float) and pd.isna(artist_field)):
        return []
    text = str(artist_field).strip()
    if not text:
        return []
    parts = _ARTIST_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def explode_artist_column(df: pd.DataFrame, col: str = "artist_name") -> pd.DataFrame:
    """One row per credited artist (for listen velocity and timelines)."""
    if df.empty or col not in df.columns:
        return df
    rows = []
    for _, r in df.iterrows():
        names = split_artist_names(r[col])
        if not names:
            continue
        for name in names:
            row = r.to_dict()
            row[col] = name
            rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def build_artist_catalog(
    artists_df: pd.DataFrame,
    tracks_df: pd.DataFrame,
    recent_df: pd.DataFrame,
    saved_tracks_df: pd.DataFrame | None = None,
    playlist_tracks: dict[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """
    Union of artists from top artists, top tracks, recent plays, saved tracks,
    and playlists — classified from Spotify API metadata only.
    """
    catalog: dict[str, dict] = {}

    def upsert(display_name: str, **fields):
        key = _norm_name(display_name)
        if not key:
            return
        if key not in catalog:
            catalog[key] = {
                "artist_name": str(display_name).strip(),
                "artist_id": "",
                "genres": [],
                "genres_str": "",
                "popularity": None,
                "followers": None,
                "external_url": "",
                "best_rank": 999,
                "genre_bucket": "",
                "region_tag": "",
                "scene_tag": "",
            }
        row = catalog[key]
        for k, v in fields.items():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            if k == "best_rank":
                row[k] = min(row[k], int(v))
            elif k == "genres" and v:
                existing = row.get("genres") or []
                if isinstance(v, list):
                    row["genres"] = list(dict.fromkeys(existing + v))
                else:
                    row["genres"] = list(dict.fromkeys(existing + _parse_genres(v)))
                row["genres_str"] = ", ".join(row["genres"])
            else:
                row[k] = v

    def _ingest_track_row(t: pd.Series):
        rank_col = "rank" if "rank" in t.index else None
        tr = int(t[rank_col]) if rank_col and pd.notna(t.get(rank_col)) else 999
        gstr = t.get("genres_str", "") or ""
        genres = t.get("genres") or _parse_genres(gstr)
        pop = t.get("popularity")
        for name in split_artist_names(t.get("artist_name", "")):
            upsert(
                name,
                best_rank=tr,
                popularity=pop,
                genres=genres if genres else None,
            )

    if not artists_df.empty:
        for _, a in artists_df.iterrows():
            name = a.get("artist_name", "")
            if not name:
                continue
            upsert(
                name,
                artist_id=a.get("artist_id", ""),
                genres=a.get("genres") or _parse_genres(a.get("genres_str")),
                popularity=a.get("popularity"),
                followers=a.get("followers"),
                external_url=a.get("external_url", ""),
                best_rank=a.get("rank", 999),
                genre_bucket=a.get("genre_bucket", ""),
                region_tag=a.get("region_tag", ""),
                scene_tag=a.get("scene_tag", ""),
            )

    for source_df in [tracks_df, recent_df, saved_tracks_df]:
        if source_df is None or source_df.empty or "artist_name" not in source_df.columns:
            continue
        for _, t in source_df.iterrows():
            _ingest_track_row(t)

    if playlist_tracks:
        for pdf in playlist_tracks.values():
            if pdf is None or pdf.empty:
                continue
            for _, t in pdf.iterrows():
                _ingest_track_row(t)

    if not catalog:
        return pd.DataFrame()

    rows = []
    for _key, row in catalog.items():
        genres = row.get("genres") or []
        gstr = row.get("genres_str", "") or ", ".join(genres)
        if not row.get("genre_bucket"):
            row["genre_bucket"] = classify_genres(genres)
        if not row.get("region_tag"):
            row["region_tag"] = classify_region(genres, row["artist_name"])
        if not row.get("scene_tag"):
            row["scene_tag"] = derive_scene_tag(gstr, row["artist_name"])
        row["languages"] = derive_languages(gstr, row["artist_name"])
        rows.append(row)

    return pd.DataFrame(rows)


def convert_duration_ms_to_min(duration_ms: int | float | None) -> float:
    if duration_ms is None or (isinstance(duration_ms, float) and pd.isna(duration_ms)):
        return 0.0
    return round(float(duration_ms) / 60000, 2)


def calculate_release_year(release_date: str | None) -> int | None:
    if not release_date or (isinstance(release_date, float) and pd.isna(release_date)):
        return None
    s = str(release_date)[:4]
    try:
        return int(s)
    except ValueError:
        return None


def _parse_genres(genres: Any) -> list[str]:
    if genres is None or (isinstance(genres, float) and pd.isna(genres)):
        return []
    if isinstance(genres, list):
        return [str(g).lower() for g in genres]
    s = str(genres).strip()
    if s.startswith("["):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(g).lower() for g in parsed]
        except (ValueError, SyntaxError):
            pass
    return [g.strip().lower() for g in s.split(",") if g.strip()]


def classify_genres(genres: list[str] | str | None) -> str:
    glist = _parse_genres(genres)
    combined = " ".join(glist)
    for kw in HIP_HOP_KEYWORDS:
        if kw in combined:
            return "Hip-Hop/Rap"
    for kw in INDIA_KEYWORDS:
        if kw in combined:
            return "India-linked"
    for bucket, keywords in INTERNATIONAL_BUCKETS.items():
        for kw in keywords:
            if kw in combined:
                return bucket
    return "Other/Unknown"


def derive_scene_tag(genres_str: str | None, artist_name: str = "") -> str:
    """Map genre text to editorial scene lane (club, techno, desi, etc.)."""
    combined = f"{genres_str or ''} {artist_name}".lower()
    for label, keywords in SCENE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return label
    return ""


def derive_languages(genres_str: str | None, artist_name: str = "") -> str:
    """Comma-separated language hints from genres and artist name."""
    combined = f"{genres_str or ''} {artist_name}".lower()
    found: list[str] = []
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            found.append(lang)
    return ", ".join(found)


def classify_region(
    genres: list[str] | str | None,
    artist_name: str = "",
    manual_row: dict | pd.Series | None = None,
) -> str:
    if manual_row is not None and pd.notna(manual_row.get("region")):
        return str(manual_row["region"])
    bucket = classify_genres(genres)
    if bucket == "India-linked":
        return "India-linked"
    name = _norm_name(artist_name)
    india_name_hints = ["desi", "punjabi", "hindi", "mumbai", "delhi"]
    if any(h in name for h in india_name_hints):
        return "India-linked"
    if bucket in INTERNATIONAL_BUCKETS or bucket == "Hip-Hop/Rap":
        return "International"
    return "Other/Unknown"


def calculate_repeat_affinity(top_artists_df: pd.DataFrame) -> pd.DataFrame:
    if top_artists_df.empty or "time_range" not in top_artists_df.columns:
        return pd.DataFrame(columns=["artist_name", "terms_present", "repeat_affinity"])

    pivot = (
        top_artists_df.groupby("artist_name")["time_range"]
        .apply(lambda x: set(x.dropna()))
        .reset_index()
    )
    pivot["terms_present"] = pivot["time_range"].apply(len)
    pivot["repeat_affinity"] = pivot["terms_present"].apply(
        lambda n: "High" if n >= 3 else "Medium" if n == 2 else "Low"
    )
    pivot.drop(columns=["time_range"], inplace=True)
    return pivot.sort_values("terms_present", ascending=False)


def normalize_tracks(
    raw_tracks: list[dict] | pd.DataFrame,
    source: str = "api",
    time_range: str | None = None,
) -> pd.DataFrame:
    rows = []
    items = raw_tracks.to_dict("records") if isinstance(raw_tracks, pd.DataFrame) else raw_tracks

    for i, item in enumerate(items):
        if source == "api" and isinstance(item, dict) and "track" in item:
            item = item.get("track") or item
        if isinstance(item, pd.Series):
            row = item.to_dict()
            rows.append(_track_row_from_flat(row, source, time_range or row.get("time_range"), i + 1))
            continue
        if "track_name" in item:
            rows.append(_track_row_from_flat(item, source, time_range or item.get("time_range"), item.get("rank", i + 1)))
            continue
        track = item if "name" in item else item.get("track", item)
        if not track:
            continue
        artists = track.get("artists", [])
        artist_name = ", ".join(a["name"] for a in artists) if artists else item.get("artist_name", "")
        artist_id = artists[0]["id"] if artists else item.get("artist_id", "")
        album = track.get("album", {}) or {}
        rows.append(
            {
                "track_id": track.get("id", item.get("track_id", "")),
                "track_name": track.get("name", item.get("track_name", "")),
                "artist_name": artist_name or item.get("artist_name", ""),
                "artist_id": artist_id,
                "album": album.get("name", item.get("album", "")),
                "popularity": track.get("popularity", item.get("popularity")),
                "release_date": album.get("release_date", item.get("release_date", "")),
                "release_year": calculate_release_year(album.get("release_date", item.get("release_date"))),
                "explicit": track.get("explicit", item.get("explicit", False)),
                "duration_ms": track.get("duration_ms", item.get("duration_ms")),
                "duration_min": convert_duration_ms_to_min(
                    track.get("duration_ms", item.get("duration_ms"))
                ),
                "external_url": (track.get("external_urls") or {}).get("spotify", item.get("external_url", "")),
                "source": source,
                "time_range": time_range or item.get("time_range"),
                "rank": item.get("rank", i + 1),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and "release_year" not in df.columns:
        df["release_year"] = df["release_date"].map(calculate_release_year)
    return df


def _track_row_from_flat(item: dict, source: str, time_range: str | None, rank: int) -> dict:
    rd = item.get("release_date", "")
    return {
        "track_id": item.get("track_id", ""),
        "track_name": item.get("track_name", ""),
        "artist_name": item.get("artist_name", ""),
        "artist_id": item.get("artist_id", ""),
        "album": item.get("album", ""),
        "popularity": item.get("popularity"),
        "release_date": rd,
        "release_year": calculate_release_year(rd),
        "explicit": item.get("explicit", False),
        "duration_ms": item.get("duration_ms"),
        "duration_min": convert_duration_ms_to_min(item.get("duration_ms")),
        "external_url": item.get("external_url", ""),
        "source": source,
        "time_range": time_range,
        "rank": rank,
    }


def normalize_artists(
    raw_artists: list[dict] | pd.DataFrame, time_range: str | None = None
) -> pd.DataFrame:
    rows = []
    items = raw_artists.to_dict("records") if isinstance(raw_artists, pd.DataFrame) else raw_artists

    for i, item in enumerate(items):
        if isinstance(item, pd.Series):
            item = item.to_dict()
        if "artist_name" in item:
            genres = _parse_genres(item.get("genres"))
            rows.append(
                {
                    "artist_id": item.get("artist_id", ""),
                    "artist_name": item.get("artist_name", ""),
                    "genres": genres,
                    "genres_str": ", ".join(genres),
                    "popularity": item.get("popularity"),
                    "followers": item.get("followers"),
                    "external_url": item.get("external_url", ""),
                    "time_range": time_range or item.get("time_range"),
                    "rank": item.get("rank", i + 1),
                    "genre_bucket": classify_genres(genres),
                    "region_tag": classify_region(genres, item.get("artist_name", "")),
                    "scene_tag": item.get("scene", ""),
                }
            )
            continue
        genres = item.get("genres", [])
        rows.append(
            {
                "artist_id": item.get("id", ""),
                "artist_name": item.get("name", ""),
                "genres": genres,
                "genres_str": ", ".join(genres),
                "popularity": item.get("popularity"),
                "followers": (item.get("followers") or {}).get("total")
                if isinstance(item.get("followers"), dict)
                else item.get("followers"),
                "external_url": (item.get("external_urls") or {}).get("spotify", ""),
                "time_range": time_range,
                "rank": i + 1,
                "genre_bucket": classify_genres(genres),
                "region_tag": classify_region(genres, item.get("name", "")),
                "scene_tag": "",
            }
        )
    return pd.DataFrame(rows)


def normalize_recently_played(raw_recent: list[dict] | pd.DataFrame) -> pd.DataFrame:
    rows = []
    items = raw_recent.to_dict("records") if isinstance(raw_recent, pd.DataFrame) else raw_recent
    for item in items:
        if isinstance(item, pd.Series):
            item = item.to_dict()
        if "track_name" in item and "played_at" in item:
            rows.append(
                {
                    "track_id": item.get("track_id", ""),
                    "track_name": item.get("track_name", ""),
                    "artist_name": item.get("artist_name", ""),
                    "album": item.get("album", ""),
                    "played_at": item.get("played_at", ""),
                    "popularity": item.get("popularity"),
                    "release_date": item.get("release_date", ""),
                    "explicit": item.get("explicit", False),
                    "duration_ms": item.get("duration_ms"),
                    "external_url": item.get("external_url", ""),
                }
            )
            continue
        track = item.get("track", {})
        played = item.get("played_at", "")
        artists = track.get("artists", [])
        artist_name = ", ".join(a["name"] for a in artists)
        album = track.get("album", {}) or {}
        rows.append(
            {
                "track_id": track.get("id", ""),
                "track_name": track.get("name", ""),
                "artist_name": artist_name,
                "album": album.get("name", ""),
                "played_at": played,
                "popularity": track.get("popularity"),
                "release_date": album.get("release_date", ""),
                "explicit": track.get("explicit", False),
                "duration_ms": track.get("duration_ms"),
                "external_url": (track.get("external_urls") or {}).get("spotify", ""),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and "played_at" in df.columns:
        df["played_at"] = pd.to_datetime(df["played_at"], errors="coerce", utc=True)
        df["play_date"] = df["played_at"].dt.date
        df["hour"] = df["played_at"].dt.hour
        df["day_of_week"] = df["played_at"].dt.day_name()
    return df


def merge_recent_history(existing: pd.DataFrame, new_batch: pd.DataFrame, max_rows: int = 200) -> pd.DataFrame:
    """Append recent plays, dedupe by track_id + played_at, keep newest."""
    if new_batch.empty:
        return existing
    if existing.empty:
        return new_batch.head(max_rows)
    combined = pd.concat([existing, new_batch], ignore_index=True)
    dedupe_cols = [c for c in ["track_id", "played_at"] if c in combined.columns]
    if dedupe_cols:
        combined = combined.drop_duplicates(subset=dedupe_cols, keep="first")
    if "played_at" in combined.columns:
        combined["played_at"] = pd.to_datetime(combined["played_at"], errors="coerce", utc=True)
        combined = combined.sort_values("played_at", ascending=False)
    return combined.head(max_rows).reset_index(drop=True)


def normalize_playlists(raw_playlists: list[dict] | pd.DataFrame) -> pd.DataFrame:
    rows = []
    items = raw_playlists.to_dict("records") if isinstance(raw_playlists, pd.DataFrame) else raw_playlists
    for item in items:
        if isinstance(item, pd.Series):
            item = item.to_dict()
        if "playlist_name" in item:
            rows.append(
                {
                    "playlist_id": item.get("playlist_id", ""),
                    "playlist_name": item.get("playlist_name", ""),
                    "track_count": item.get("track_count"),
                    "owner": item.get("owner", ""),
                    "public": item.get("public"),
                    "description": item.get("description", ""),
                }
            )
            continue
        owner = item.get("owner", {})
        rows.append(
            {
                "playlist_id": item.get("id", ""),
                "playlist_name": item.get("name", ""),
                "track_count": (item.get("tracks") or {}).get("total", item.get("track_count")),
                "owner": owner.get("display_name", "") if isinstance(owner, dict) else str(owner),
                "public": item.get("public"),
                "description": item.get("description", ""),
            }
        )
    return pd.DataFrame(rows)


def normalize_playlist_tracks(raw_items: list[dict] | pd.DataFrame, playlist_id: str = "", playlist_name: str = "") -> pd.DataFrame:
    rows = []
    items = raw_items.to_dict("records") if isinstance(raw_items, pd.DataFrame) else raw_items
    for i, item in enumerate(items):
        if isinstance(item, pd.Series):
            item = item.to_dict()
        if "track_name" in item:
            row = _track_row_from_flat(item, "api", None, item.get("position", i))
            row["playlist_id"] = item.get("playlist_id", playlist_id)
            row["playlist_name"] = item.get("playlist_name", playlist_name)
            row["position"] = item.get("position", i)
            rows.append(row)
            continue
        track = item.get("track") or item
        if not track or track.get("is_local"):
            continue
        artists = track.get("artists", [])
        album = track.get("album", {}) or {}
        rows.append(
            {
                "playlist_id": playlist_id,
                "playlist_name": playlist_name,
                "track_id": track.get("id", ""),
                "track_name": track.get("name", ""),
                "artist_name": ", ".join(a["name"] for a in artists),
                "album": album.get("name", ""),
                "popularity": track.get("popularity"),
                "release_date": album.get("release_date", ""),
                "release_year": calculate_release_year(album.get("release_date")),
                "explicit": track.get("explicit", False),
                "duration_ms": track.get("duration_ms"),
                "duration_min": convert_duration_ms_to_min(track.get("duration_ms")),
                "position": i,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        for c in ["genre_bucket", "region_tag"]:
            if c not in df.columns:
                df[c] = ""
    return df


def load_csv_safe(path, required: list[str] | None = None) -> tuple[pd.DataFrame, str | None]:
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return pd.DataFrame(), f"File not found: {p}. Connect Spotify or upload a CSV export."
    try:
        df = pd.read_csv(p)
    except Exception as e:
        return pd.DataFrame(), f"Could not read {p}: {e}"
    if required:
        missing = [c for c in required if c not in df.columns]
        if missing:
            return df, f"Missing columns: {', '.join(missing)}"
    return df, None


def empty_data_bundle() -> dict[str, Any]:
    """Initial session state — no filler rows until Spotify API or CSV upload."""
    return {
        "data_source": "none",
        "user_profile": {},
        "tracks": pd.DataFrame(),
        "artists": pd.DataFrame(),
        "recent": pd.DataFrame(),
        "saved_tracks": pd.DataFrame(),
        "playlists": pd.DataFrame(),
        "playlist_tracks": {},
        "youtube": pd.DataFrame(),
        "recent_history": pd.DataFrame(),
        "exportify_master": pd.DataFrame(),
        "exportify_stats": {},
        "data_bootstrap_complete": False,
        "bootstrap_messages": [],
        "bootstrap_at": "",
        "genre_enrichment_status": "",
    }


def enrich_tracks_with_artist_metadata(tracks_df: pd.DataFrame, artists_df: pd.DataFrame) -> pd.DataFrame:
    if tracks_df.empty or artists_df.empty:
        return tracks_df
    primary = artists_df.drop_duplicates("artist_name").set_index("artist_name")
    out = tracks_df.copy()

    def _lookup_meta(artist_field: str, col: str) -> str:
        for name in split_artist_names(artist_field):
            if name in primary.index and col in primary.columns:
                val = primary.loc[name, col]
                if pd.notna(val) and str(val).strip():
                    return str(val)
        return ""

    for col in ["genre_bucket", "region_tag", "scene_tag"]:
        if col in primary.columns:
            out[col] = out["artist_name"].map(lambda a: _lookup_meta(a, col))
    return out


def aggregate_playlist_stats(playlist_tracks_df: pd.DataFrame, artists_df: pd.DataFrame) -> dict:
    if playlist_tracks_df.empty:
        return {}
    df = enrich_tracks_with_artist_metadata(playlist_tracks_df, artists_df)
    pop = pd.to_numeric(df["popularity"], errors="coerce") if "popularity" in df.columns else pd.Series(dtype=float)
    years = pd.to_numeric(df["release_year"], errors="coerce") if "release_year" in df.columns else pd.Series(dtype=float)
    current_year = datetime.now().year
    explicit = df.get("explicit", pd.Series([False] * len(df))).astype(bool)
    region = df.get("region_tag", pd.Series(dtype=str))

    india_mask = region.astype(str).str.contains("India", case=False, na=False)
    intl_mask = region.astype(str).str.contains("International|Global", case=False, na=False)

    return {
        "track_count": len(df),
        "avg_popularity": float(pop.mean()) if pop.notna().any() else 0,
        "explicit_ratio": float(explicit.mean()) if len(explicit) else 0,
        "median_release_year": float(years.median()) if years.notna().any() else None,
        "recency_pct": float((years >= current_year - 2).mean() * 100) if years.notna().any() else 0,
        "discovery_pct": float((pop < 40).mean() * 100) if pop.notna().any() else 0,
        "india_share": float(india_mask.mean() * 100) if len(region) else 0,
        "intl_share": float(intl_mask.mean() * 100) if len(region) else 0,
        "top_artists": df["artist_name"].value_counts().head(5).to_dict() if "artist_name" in df.columns else {},
    }
