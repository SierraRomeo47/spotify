"""Session state bootstrap and Spotify data loading."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from config import (
    AUTO_ENRICH_GENRES,
    EXPORTIFY_PLAYLISTS_DIR,
    SPOTIFY_CACHE_PATH,
    TIME_RANGES,
)
import config
from data_processing import (
    build_artist_catalog,
    empty_data_bundle,
    merge_recent_history,
    normalize_artists,
    normalize_playlist_tracks,
    normalize_playlists,
    normalize_recently_played,
    normalize_tracks,
)
from exportify_loader import (
    get_exportify_bundle,
    is_exportify_dataframe,
    merge_api_with_exportify,
    normalize_exportify_dataframe,
)
from library_loader import load_local_library_bundle
from spotify_account_loader import account_data_available, clear_account_bundle_cache
from metadata_enrichment import auto_enrich_catalog
from spotify_auth import check_credentials, get_spotify_client
from spotify_fetch import (
    fetch_playlist_tracks,
    fetch_recently_played,
    fetch_saved_tracks,
    fetch_top_artists,
    fetch_top_tracks,
    fetch_user_playlists,
    fetch_user_profile,
    get_token_id,
)
from utils.io import export_csv


SESSION_KEYS = [
    "data_source",
    "user_profile",
    "tracks",
    "artists",
    "recent",
    "saved_tracks",
    "playlists",
    "playlist_tracks",
    "youtube",
    "dj_story",
    "recent_history",
    "initialized",
    "exportify_master",
    "exportify_stats",
    "data_bootstrap_complete",
    "bootstrap_messages",
    "bootstrap_at",
    "genre_enrichment_status",
]


def init_session():
    if st.session_state.get("initialized"):
        return
    data = empty_data_bundle()
    for k, v in data.items():
        st.session_state[k] = v
    from config import DEFAULT_DJ_STORY

    st.session_state.setdefault("dj_story", DEFAULT_DJ_STORY)
    st.session_state["initialized"] = True
    if config.AUTO_BOOTSTRAP_DATA:
        bootstrap_data()


def apply_data_bundle(bundle: dict):
    for k, v in bundle.items():
        st.session_state[k] = v
    st.session_state["initialized"] = True


def _rebuild_artist_catalog():
    st.session_state["artists"] = build_artist_catalog(
        st.session_state.get("artists", pd.DataFrame()),
        st.session_state.get("tracks", pd.DataFrame()),
        st.session_state.get("recent", pd.DataFrame()),
        st.session_state.get("saved_tracks"),
        st.session_state.get("playlist_tracks"),
    )


def _apply_exportify_merge():
    """Merge exportify_master into API frames and rebuild catalog."""
    master = st.session_state.get("exportify_master", pd.DataFrame())
    if master.empty:
        return

    tracks = st.session_state.get("tracks", pd.DataFrame())
    if not tracks.empty:
        st.session_state["tracks"] = merge_api_with_exportify(tracks, master)

    saved = st.session_state.get("saved_tracks", pd.DataFrame())
    if not saved.empty:
        st.session_state["saved_tracks"] = merge_api_with_exportify(saved, master)
    elif not master.empty and st.session_state.get("data_source") == "exportify":
        st.session_state["saved_tracks"] = master.copy()

    pl_map = st.session_state.get("playlist_tracks") or {}
    enriched = {}
    for pid, pdf in pl_map.items():
        enriched[pid] = merge_api_with_exportify(pdf, master) if not pdf.empty else pdf
    st.session_state["playlist_tracks"] = enriched

    recent = st.session_state.get("recent", pd.DataFrame())
    if not recent.empty:
        st.session_state["recent"] = merge_api_with_exportify(recent, master)

    _rebuild_artist_catalog()


def _local_data_available() -> bool:
    if account_data_available():
        return True
    return EXPORTIFY_PLAYLISTS_DIR.exists() and any(EXPORTIFY_PLAYLISTS_DIR.glob("*.csv"))


def _exportify_dir_has_csvs() -> bool:
    return _local_data_available()


def load_local_library(force_reload: bool = False) -> dict:
    """Load my_spotify_data (+ optional Exportify enrichment) into session."""
    if force_reload:
        clear_account_bundle_cache()
        from exportify_loader import clear_exportify_bundle_cache

        clear_exportify_bundle_cache()

    bundle = load_local_library_bundle()
    stats = bundle.get("exportify_stats", {})

    st.session_state["exportify_master"] = bundle["exportify_master"]
    st.session_state["exportify_stats"] = stats
    st.session_state["exportify_loaded_at"] = datetime.now(timezone.utc).isoformat()
    st.session_state["tracks"] = bundle.get("tracks", pd.DataFrame())
    st.session_state["artists"] = bundle.get("artists", pd.DataFrame())
    st.session_state["recent"] = bundle.get("recent", pd.DataFrame())
    st.session_state["recent_history"] = bundle.get("recent_history", bundle.get("recent", pd.DataFrame()))
    st.session_state["saved_tracks"] = bundle.get("saved_tracks", pd.DataFrame())
    st.session_state["playlists"] = bundle.get("playlists", pd.DataFrame())
    st.session_state["playlist_tracks"] = bundle.get("playlist_tracks") or {}
    st.session_state["data_source"] = bundle.get("data_source", "account")

    _apply_exportify_merge()
    return stats


def load_exportify_library(force_reload: bool = False) -> dict:
    """Backward-compatible alias — loads full local library bundle."""
    return load_local_library(force_reload=force_reload)


def run_bootstrap_steps(
    *,
    exportify_available: bool,
    spotify_credentials: bool,
    spotify_cache_exists: bool,
    auto_enrich: bool,
) -> list[str]:
    """Pure bootstrap step order for tests (no Streamlit). Returns warning messages."""
    messages: list[str] = []
    if exportify_available:
        messages.append("exportify:load")
    if spotify_credentials:
        messages.append("spotify:fetch")
    if auto_enrich:
        messages.append("enrich:genres")
    return messages


def bootstrap_data(force: bool = False) -> list[str]:
    """
    Auto-load Exportify, Spotify API, and optional genre enrichment once per session.
    Returns list of warnings/errors (non-fatal).
    """
    if st.session_state.get("data_bootstrap_complete") and not force:
        return st.session_state.get("bootstrap_messages", [])

    errors: list[str] = []

    if _local_data_available():
        try:
            load_local_library(force_reload=force)
        except Exception as ex:
            errors.append(f"Local library load: {ex}")
    else:
        errors.append("Local data: add my_spotify_data/ or Exportify CSVs in spotify_playlists/")

    if check_credentials():
        cache_exists = Path(SPOTIFY_CACHE_PATH).exists()
        open_browser = not cache_exists
        api_errors = fetch_all_spotify_data(
            open_browser=open_browser,
            skip_exportify_reload=True,
        )
        errors.extend(api_errors)
    else:
        errors.append("Spotify: add SPOTIPY_CLIENT_ID/SECRET to .env for live API data.")

    if AUTO_ENRICH_GENRES:
        artists = st.session_state.get("artists", pd.DataFrame())
        if artists is not None and not artists.empty:
            try:
                updated, status = auto_enrich_catalog(artists)
                st.session_state["artists"] = updated
                st.session_state["genre_enrichment_status"] = status
            except Exception as ex:
                errors.append(f"Genre enrichment: {ex}")
                st.session_state["genre_enrichment_status"] = str(ex)

    st.session_state["data_bootstrap_complete"] = True
    st.session_state["bootstrap_at"] = datetime.now(timezone.utc).isoformat()
    st.session_state["bootstrap_messages"] = errors
    return errors


def load_from_uploads(
    tracks_file=None,
    artists_file=None,
    recent_file=None,
    playlists_file=None,
):
    tracks_list = []
    if tracks_file:
        df = pd.read_csv(tracks_file)
        if is_exportify_dataframe(df):
            tracks_list.append(normalize_exportify_dataframe(df))
        else:
            tracks_list.append(normalize_tracks(df, source="upload"))
    artists_list = []
    if artists_file:
        df = pd.read_csv(artists_file)
        artists_list.append(normalize_artists(df))

    if tracks_list:
        st.session_state["tracks"] = pd.concat(tracks_list, ignore_index=True)
    if artists_list:
        st.session_state["artists"] = pd.concat(artists_list, ignore_index=True)
    if recent_file:
        df = pd.read_csv(recent_file)
        if is_exportify_dataframe(df):
            st.session_state["recent"] = normalize_exportify_dataframe(df)
        else:
            st.session_state["recent"] = normalize_recently_played(df)
        st.session_state["recent_history"] = st.session_state["recent"]
    if playlists_file:
        df = pd.read_csv(playlists_file)
        st.session_state["playlists"] = normalize_playlists(df)

    master = st.session_state.get("exportify_master", pd.DataFrame())
    if not master.empty:
        _apply_exportify_merge()
    else:
        _rebuild_artist_catalog()

    st.session_state["data_source"] = "upload"


def fetch_all_spotify_data(
    open_browser: bool | None = None,
    skip_exportify_reload: bool = False,
) -> list[str]:
    """Fetch from API and update session. Returns list of errors."""
    errors = []
    if open_browser is None:
        open_browser = not Path(SPOTIFY_CACHE_PATH).exists()

    sp, err = get_spotify_client(open_browser=open_browser)
    if err:
        return [err]
    try:
        token_id = get_token_id(sp)
    except Exception as e:
        return [str(e)]

    profile, e = fetch_user_profile(token_id, sp)
    if e:
        errors.append(f"Profile: {e}")
    if profile:
        st.session_state["user_profile"] = profile

    all_tracks = []
    all_artists = []
    for tr in TIME_RANGES:
        raw_t, e = fetch_top_tracks(token_id, sp, tr)
        if e:
            errors.append(f"Top tracks ({tr}): {e}")
        all_tracks.append(normalize_tracks(raw_t, "api", tr))
        raw_a, e = fetch_top_artists(token_id, sp, tr)
        if e:
            errors.append(f"Top artists ({tr}): {e}")
        all_artists.append(normalize_artists(raw_a, tr))

    st.session_state["tracks"] = pd.concat(all_tracks, ignore_index=True) if all_tracks else pd.DataFrame()
    artists = pd.concat(all_artists, ignore_index=True) if all_artists else pd.DataFrame()

    raw_r, e = fetch_recently_played(token_id, sp)
    if e:
        errors.append(f"Recently played: {e}")
    recent_batch = normalize_recently_played(raw_r)
    prev = st.session_state.get("recent_history", pd.DataFrame())
    if st.session_state.get("data_source") in ("none", "exportify"):
        prev = pd.DataFrame()
    merged = merge_recent_history(prev, recent_batch)
    st.session_state["recent_history"] = merged
    st.session_state["recent"] = merged if not merged.empty else recent_batch

    raw_s, e = fetch_saved_tracks(token_id, sp, limit=500)
    if e:
        errors.append(f"Saved tracks: {e}")
    saved_tracks = normalize_tracks([x.get("track", x) for x in raw_s], "api", None)
    st.session_state["saved_tracks"] = saved_tracks

    raw_p, e = fetch_user_playlists(token_id, sp)
    if e:
        errors.append(f"Playlists: {e}")
    playlists = normalize_playlists(raw_p)
    st.session_state["playlists"] = playlists

    playlist_tracks = {}
    for _, row in playlists.head(15).iterrows():
        pid = row["playlist_id"]
        pname = row["playlist_name"]
        items, pe = fetch_playlist_tracks(token_id, sp, pid)
        if pe:
            errors.append(f"Playlist {pname}: {pe}")
        playlist_tracks[pid] = normalize_playlist_tracks(items, pid, pname)

    exp_pl = st.session_state.get("playlist_tracks") or {}
    if isinstance(exp_pl, dict) and exp_pl:
        playlist_tracks = {**exp_pl, **playlist_tracks}
    st.session_state["playlist_tracks"] = playlist_tracks

    prev_source = st.session_state.get("data_source", "none")
    if prev_source in ("exportify", "api+exportify"):
        st.session_state["data_source"] = "api+exportify"
    else:
        st.session_state["data_source"] = "api"

    st.session_state["artists"] = build_artist_catalog(
        artists,
        st.session_state["tracks"],
        st.session_state["recent"],
        saved_tracks,
        playlist_tracks,
    )

    _export_session_csvs()

    if skip_exportify_reload:
        if not st.session_state.get("exportify_master", pd.DataFrame()).empty:
            _apply_exportify_merge()
    elif _exportify_dir_has_csvs():
        try:
            load_exportify_library()
        except Exception as ex:
            errors.append(f"Exportify merge: {ex}")

    return errors


def _export_session_csvs():
    if not st.session_state.get("tracks", pd.DataFrame()).empty:
        export_csv(st.session_state["tracks"], "top_tracks_export.csv")
    if not st.session_state.get("artists", pd.DataFrame()).empty:
        export_csv(st.session_state["artists"], "top_artists_export.csv")
    if not st.session_state.get("recent", pd.DataFrame()).empty:
        export_csv(st.session_state["recent"], "recently_played_export.csv")
