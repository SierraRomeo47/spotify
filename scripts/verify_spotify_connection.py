#!/usr/bin/env python
"""
Verify .env configuration and Spotify API data loading.
Run from project root: python scripts/verify_spotify_connection.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def mask(s: str) -> str:
    if not s:
        return "(empty)"
    return f"{s[:4]}...{s[-4:]}" if len(s) > 8 else "(set)"


def main() -> int:
    print("=== Sierra Romeo — Spotify connection verify ===\n")

    cid = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
    secret = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()
    uri = os.getenv("SPOTIPY_REDIRECT_URI", "").strip()

    print(f"SPOTIPY_CLIENT_ID:     {mask(cid)}")
    print(f"SPOTIPY_CLIENT_SECRET: {mask(secret)}")
    print(f"SPOTIPY_REDIRECT_URI:  {uri or '(empty)'}")

    if not cid or not secret:
        print("\nFAIL: Client ID or Secret is empty in .env")
        print("Edit: sierra_romeo_editorial_lab/.env")
        print("  SPOTIPY_CLIENT_ID=your_id_here")
        print("  SPOTIPY_CLIENT_SECRET=your_secret_here")
        return 1

    if uri != "http://127.0.0.1:8888/callback":
        print("\nWARN: Redirect URI should be http://127.0.0.1:8888/callback")

    cache = ROOT / ".spotify_cache"
    print(f"\nOAuth cache (.spotify_cache): {'found' if cache.exists() else 'not found'}")

    from spotify_auth import get_spotify_client
    from data_processing import normalize_artists, normalize_tracks
    from spotify_fetch import fetch_top_artists, fetch_top_tracks, fetch_user_profile, get_token_id

    sp, err = get_spotify_client(open_browser=not cache.exists())
    if err:
        print(f"\nFAIL: Could not create client: {err}")
        return 1

    try:
        profile, err = fetch_user_profile("verify", sp)
        if err:
            print(f"\nFAIL: current_user — {err}")
            if not cache.exists():
                print("Complete browser login when prompted, then re-run this script.")
            return 1
        print(f"\nOK: Logged in as {profile.get('display_name')} (id={profile.get('id')})")

        token_id = get_token_id(sp)
        tracks, err = fetch_top_tracks(token_id, sp, "short_term", 5)
        if err:
            print(f"WARN: top tracks — {err}")
        else:
            df = normalize_tracks(tracks, "api", "short_term")
            print(f"OK: Top tracks ({len(df)} rows), e.g. {df['track_name'].iloc[0] if len(df) else '—'}")

        artists, err = fetch_top_artists(token_id, sp, "short_term", 5)
        if err:
            print(f"WARN: top artists — {err}")
        else:
            df = normalize_artists(artists, "short_term")
            print(f"OK: Top artists ({len(df)} rows), e.g. {df['artist_name'].iloc[0] if len(df) else '—'}")

        print("\nAll checks passed. Use Data Source page in Streamlit to fetch full dataset.")
        return 0
    except Exception as e:
        print(f"\nFAIL: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
