"""Unified local data loading: my_spotify_data (primary) + optional Exportify enrichment."""

from __future__ import annotations

from typing import Any

import pandas as pd

from config import EXPORTIFY_PLAYLISTS_DIR, OUTPUTS_DIR, TIME_RANGES
from data_processing import build_artist_catalog, normalize_recently_played, normalize_tracks
from exportify_loader import build_enrichment_master, get_exportify_bundle, merge_api_with_exportify
from spotify_account_loader import (
    account_data_available,
    get_spotify_account_bundle,
)


def _exportify_csvs_available() -> bool:
    return EXPORTIFY_PLAYLISTS_DIR.exists() and any(EXPORTIFY_PLAYLISTS_DIR.glob("*.csv"))


def _load_api_exports() -> dict[str, pd.DataFrame]:
    """Optional fresher API CSV exports from outputs/."""
    tracks_path = OUTPUTS_DIR / "top_tracks_export.csv"
    artists_path = OUTPUTS_DIR / "top_artists_export.csv"
    recent_path = OUTPUTS_DIR / "recently_played_export.csv"
    out: dict[str, pd.DataFrame] = {
        "tracks": pd.DataFrame(),
        "artists": pd.DataFrame(),
        "recent": pd.DataFrame(),
    }

    if tracks_path.exists():
        raw = pd.read_csv(tracks_path)
        if "time_range" in raw.columns:
            parts = [raw[raw["time_range"] == tr] for tr in TIME_RANGES if not raw[raw["time_range"] == tr].empty]
            out["tracks"] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        else:
            out["tracks"] = normalize_tracks(raw, "api", None)

    if artists_path.exists():
        out["artists"] = pd.read_csv(artists_path)

    if recent_path.exists():
        raw_recent = pd.read_csv(recent_path)
        if "played_at" in raw_recent.columns and "artist_name" in raw_recent.columns:
            out["recent"] = raw_recent
        else:
            out["recent"] = normalize_recently_played(raw_recent.to_dict("records"))

    return out


def _merge_enrichment(master: pd.DataFrame, *frames: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    if master.empty:
        return frames
    return tuple(merge_api_with_exportify(f, master) if f is not None and not f.empty else f for f in frames)


def load_local_library_bundle() -> dict[str, Any]:
    """
    Primary: my_spotify_data privacy export.
    Enrichment: Exportify CSV genres/popularity/audio when spotify_playlists/ exists.
    Override: outputs/*.csv from live API when present.
    """
    data_source = "none"
    account_stats: dict[str, Any] = {}
    exportify_stats: dict[str, Any] = {}

    tracks = pd.DataFrame()
    artists = pd.DataFrame()
    recent = pd.DataFrame()
    saved_tracks = pd.DataFrame()
    playlist_tracks: dict[str, pd.DataFrame] = {}
    playlists = pd.DataFrame()
    master = pd.DataFrame()

    if account_data_available():
        account = get_spotify_account_bundle()
        data_source = "account"
        account_stats = account.get("stats", {})
        master = account.get("exportify_master", pd.DataFrame())
        saved_tracks = account.get("saved_tracks", pd.DataFrame())
        playlist_tracks = dict(account.get("playlist_tracks") or {})
        playlists = account.get("playlists", pd.DataFrame())
        tracks = account.get("tracks", pd.DataFrame())
        artists = account.get("artists", pd.DataFrame())
        recent = account.get("recent", pd.DataFrame())

    if _exportify_csvs_available():
        exp = get_exportify_bundle()
        exportify_stats = exp.get("stats", {})
        exp_master = exp.get("exportify_master", pd.DataFrame())
        if not exp_master.empty:
            master = build_enrichment_master(master, exp_master) if not master.empty else exp_master
        if data_source == "account":
            data_source = "account+exportify"
        elif data_source == "none":
            data_source = "exportify"
            saved_tracks = exp.get("saved_tracks", pd.DataFrame())
            playlist_tracks = dict(exp.get("playlist_tracks") or {})
            playlists = exp.get("playlists", pd.DataFrame())
            master = exp_master if not exp_master.empty else master

    api = _load_api_exports()
    if not api["tracks"].empty or not api["artists"].empty or not api["recent"].empty:
        if not api["tracks"].empty:
            tracks = api["tracks"]
        if not api["artists"].empty:
            artists = api["artists"]
        if not api["recent"].empty:
            recent = api["recent"]
        if data_source in ("none", "exportify"):
            data_source = "api+exportify" if data_source == "exportify" else "api"
        else:
            data_source = f"{data_source}+api"

    tracks, saved_tracks, recent = _merge_enrichment(master, tracks, saved_tracks, recent)
    enriched_pl: dict[str, pd.DataFrame] = {}
    for pid, pdf in playlist_tracks.items():
        enriched_pl[pid] = merge_api_with_exportify(pdf, master) if not pdf.empty and not master.empty else pdf
    playlist_tracks = enriched_pl

    if artists.empty and (not tracks.empty or not recent.empty):
        artists = pd.DataFrame()

    artists = build_artist_catalog(artists, tracks, recent, saved_tracks, playlist_tracks)

    stats = {**account_stats, **exportify_stats}
    stats["master_tracks"] = len(master)

    return {
        "data_source": data_source,
        "exportify_master": master,
        "exportify_stats": stats,
        "tracks": tracks,
        "artists": artists,
        "recent": recent,
        "recent_history": recent,
        "saved_tracks": saved_tracks,
        "playlists": playlists,
        "playlist_tracks": playlist_tracks,
    }
