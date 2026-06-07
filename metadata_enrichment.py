"""Optional external metadata enrichment for artists missing genres (MusicBrainz, Last.fm)."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

from config import ENRICHMENT_CACHE_PATH, ROOT_DIR
from data_processing import _parse_genres, classify_genres, classify_region, derive_languages, derive_scene_tag

USER_AGENT = "SierraRomeoEditorialLab/1.0 (portfolio; contact@example.com)"
MUSICBRAINZ_DELAY_SEC = 1.1


def _load_cache(path: Path | None = None) -> dict[str, Any]:
    p = path or ENRICHMENT_CACHE_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict[str, Any], path: Path | None = None) -> None:
    p = path or ENRICHMENT_CACHE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _http_get_json(url: str, headers: dict | None = None) -> dict | list | None:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def fetch_musicbrainz_artist_tags(artist_name: str) -> list[str]:
    cache_key = f"mb:{artist_name.lower()}"
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key].get("tags", [])

    q = urllib.parse.quote(artist_name)
    search_url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{q}&fmt=json&limit=1"
    data = _http_get_json(search_url)
    time.sleep(MUSICBRAINZ_DELAY_SEC)
    if not data or not data.get("artists"):
        cache[cache_key] = {"tags": []}
        _save_cache(cache)
        return []

    mbid = data["artists"][0].get("id")
    if not mbid:
        return []

    tag_url = f"https://musicbrainz.org/ws/2/artist/{mbid}?inc=tags&fmt=json"
    detail = _http_get_json(tag_url)
    time.sleep(MUSICBRAINZ_DELAY_SEC)
    tags = []
    if detail and detail.get("tags"):
        tags = [t.get("name", "").lower() for t in detail["tags"] if t.get("name")][:8]
    cache[cache_key] = {"tags": tags}
    _save_cache(cache)
    return tags


def fetch_lastfm_artist_tags(artist_name: str) -> list[str]:
    api_key = os.getenv("LASTFM_API_KEY", "").strip()
    if not api_key:
        return []

    cache_key = f"lfm:{artist_name.lower()}"
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key].get("tags", [])

    q = urllib.parse.quote(artist_name)
    url = (
        f"https://ws.audioscrobbler.com/2.0/?method=artist.getTopTags"
        f"&artist={q}&api_key={api_key}&format=json"
    )
    data = _http_get_json(url)
    tags = []
    if data and data.get("toptags", {}).get("tag"):
        raw = data["toptags"]["tag"]
        if isinstance(raw, dict):
            raw = [raw]
        tags = [t.get("name", "").lower() for t in raw if t.get("name")][:8]
    cache[cache_key] = {"tags": tags}
    _save_cache(cache)
    return tags


def enrich_artist_tags(artist_name: str) -> tuple[list[str], str]:
    """Return (genre list, source label)."""
    tags = fetch_musicbrainz_artist_tags(artist_name)
    source = "musicbrainz"
    if not tags:
        tags = fetch_lastfm_artist_tags(artist_name)
        source = "lastfm" if tags else ""
    return tags, source


def enrich_sparse_artists(
    catalog_df: pd.DataFrame,
    max_artists: int = 25,
    cache_path: Path | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Fill empty genres_str for up to max_artists rows using MusicBrainz then Last.fm.
    Returns updated catalog and status message.
    """
    if catalog_df.empty or "artist_name" not in catalog_df.columns:
        return catalog_df, "No artist catalog to enrich."

    if "genres_str" not in catalog_df.columns:
        catalog_df = catalog_df.copy()
        catalog_df["genres_str"] = ""

    mask = catalog_df["genres_str"].fillna("").astype(str).str.strip() == ""
    sparse = catalog_df[mask].head(max_artists)
    if sparse.empty:
        return catalog_df, "No artists missing genres."

    out = catalog_df.copy()
    enriched = 0
    for idx, row in sparse.iterrows():
        name = row["artist_name"]
        tags, _src = enrich_artist_tags(name)
        if not tags:
            continue
        gstr = ", ".join(tags)
        out.at[idx, "genres_str"] = gstr
        out.at[idx, "genre_bucket"] = classify_genres(tags)
        out.at[idx, "region_tag"] = classify_region(tags, name)
        out.at[idx, "scene_tag"] = derive_scene_tag(gstr, name)
        out.at[idx, "languages"] = derive_languages(gstr, name)
        enriched += 1

    return out, f"Enriched {enriched} of {len(sparse)} artists (cap {max_artists})."


def auto_enrich_catalog(catalog_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Enrich sparse genres; prioritize artists by best_rank (live taste first)."""
    from config import ENRICH_MAX_ARTISTS_BOOTSTRAP

    if catalog_df.empty:
        return catalog_df, "No catalog to enrich."

    df = catalog_df.copy()
    if "genres_str" not in df.columns:
        df["genres_str"] = ""

    mask = df["genres_str"].fillna("").astype(str).str.strip() == ""
    sparse = df[mask]
    if sparse.empty:
        return catalog_df, "No artists missing genres."

    if "best_rank" in sparse.columns:
        sparse = sparse.sort_values("best_rank", ascending=True)

    target_idx = sparse.index[:ENRICH_MAX_ARTISTS_BOOTSTRAP]
    subset = df.loc[target_idx]
    enriched_subset, msg = enrich_sparse_artists(subset, max_artists=ENRICH_MAX_ARTISTS_BOOTSTRAP)
    out = catalog_df.copy()
    for idx in enriched_subset.index:
        for col in enriched_subset.columns:
            out.at[idx, col] = enriched_subset.at[idx, col]
    return out, msg
