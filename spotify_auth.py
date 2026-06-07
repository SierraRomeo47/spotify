"""Spotify OAuth helpers."""

import os
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import ROOT_DIR, SCOPES, SPOTIFY_CACHE_PATH


def check_credentials() -> bool:
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env", override=True)
    cid = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
    secret = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()
    return bool(cid and secret)


def get_spotify_client(open_browser: bool = True):
    """Return (spotipy.Spotify client, error_message)."""
    if not check_credentials():
        return None, "Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in .env"
    try:
        auth_manager = SpotifyOAuth(
            scope=SCOPES,
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
            cache_path=SPOTIFY_CACHE_PATH,
            open_browser=open_browser,
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp, None
    except Exception as e:
        return None, str(e)


def clear_cache():
    cache = Path(SPOTIFY_CACHE_PATH)
    if cache.exists():
        cache.unlink()
    try:
        from exportify_loader import clear_exportify_bundle_cache
        from spotify_account_loader import clear_account_bundle_cache

        clear_exportify_bundle_cache()
        clear_account_bundle_cache()
    except Exception:
        pass
    try:
        import streamlit as st

        st.cache_data.clear()
    except Exception:
        pass
