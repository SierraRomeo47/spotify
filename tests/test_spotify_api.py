"""Spotify API integration tests (requires .env + OAuth cache)."""

import os
from pathlib import Path

import pytest

from config import ROOT_DIR
from data_processing import normalize_artists, normalize_recently_played, normalize_tracks
from spotify_auth import check_credentials, get_spotify_client

# Direct fetch helpers without Streamlit cache
from spotify_fetch import (
    fetch_recently_played,
    fetch_top_artists,
    fetch_top_tracks,
    fetch_user_playlists,
    fetch_user_profile,
    get_token_id,
)

FORBIDDEN_METHODS = [
    "audio_features",
    "audio_analysis",
    "recommendations",
    "related_artists",
]


def _credentials_configured():
    return check_credentials()


def _has_oauth_cache():
    return (ROOT_DIR / ".spotify_cache").exists()


@pytest.mark.skipif(not _credentials_configured(), reason="SPOTIPY_CLIENT_ID/SECRET not set in .env")
class TestSpotifyCredentials:
    def test_client_initializes(self):
        sp, err = get_spotify_client(open_browser=False)
        assert err is None, err
        assert sp is not None


@pytest.mark.skipif(
    not (_credentials_configured() and _has_oauth_cache()),
    reason="Need .env credentials and .spotify_cache (run app Connect once)",
)
class TestSpotifyLiveData:
    @pytest.fixture
    def sp(self):
        sp, err = get_spotify_client(open_browser=False)
        if err:
            pytest.skip(err)
        return sp

    def test_no_forbidden_api_methods_on_client(self, sp):
        for name in FORBIDDEN_METHODS:
            assert not hasattr(sp, name) or name not in str(type(sp))

    def test_current_user(self, sp):
        profile, err = fetch_user_profile("test", sp)
        assert err is None, err
        assert profile.get("id")
        assert profile.get("display_name")

    def test_top_tracks_normalized(self, sp):
        token_id = get_token_id(sp)
        raw, err = fetch_top_tracks(token_id, sp, "medium_term", 10)
        assert err is None, err
        assert len(raw) > 0
        df = normalize_tracks(raw, "api", "medium_term")
        assert "track_name" in df.columns
        assert df["track_name"].notna().all()
        # popularity may be absent for some tracks in dev/restricted responses
        if "popularity" in df.columns:
            assert len(df) > 0

    def test_top_artists_normalized(self, sp):
        token_id = get_token_id(sp)
        raw, err = fetch_top_artists(token_id, sp, "medium_term", 10)
        assert err is None, err
        assert len(raw) > 0
        df = normalize_artists(raw, "medium_term")
        assert "artist_name" in df.columns

    def test_recently_played_normalized(self, sp):
        token_id = get_token_id(sp)
        raw, err = fetch_recently_played(token_id, sp, 20)
        if err and "403" in err:
            pytest.skip(f"Recently played unavailable: {err}")
        assert err is None, err
        df = normalize_recently_played(raw)
        if not df.empty:
            assert "played_at" in df.columns

    def test_playlists(self, sp):
        token_id = get_token_id(sp)
        raw, err = fetch_user_playlists(token_id, sp, 10)
        assert err is None, err
        assert isinstance(raw, list)
