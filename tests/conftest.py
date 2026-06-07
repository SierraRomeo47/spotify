"""Pytest configuration — load .env from project root."""

import sys
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")


@pytest.fixture(autouse=True)
def disable_auto_bootstrap(monkeypatch):
    """Avoid loading real data / Spotify OAuth when tests import streamlit_app."""
    monkeypatch.setattr("config.AUTO_BOOTSTRAP_DATA", False)


@pytest.fixture
def project_root():
    return ROOT


@pytest.fixture
def api_fixture_bundle():
    """Minimal normalized API-shaped data for unit tests only (not loaded at runtime)."""
    from data_processing import build_artist_catalog

    tracks = pd.DataFrame(
        [
            {
                "track_id": "t1",
                "track_name": "Mirchi",
                "artist_name": "Divine",
                "time_range": "long_term",
                "rank": 1,
                "popularity": 66,
                "release_year": 2019,
                "release_date": "2019-05-17",
                "explicit": True,
                "duration_min": 3.3,
            },
            {
                "track_id": "t2",
                "track_name": "Delilah",
                "artist_name": "Fred again..",
                "time_range": "short_term",
                "rank": 1,
                "popularity": 78,
                "release_year": 2023,
                "release_date": "2023-10-06",
                "explicit": False,
                "duration_min": 4.0,
            },
            {
                "track_id": "t3",
                "track_name": "295",
                "artist_name": "Shubh",
                "time_range": "long_term",
                "rank": 2,
                "popularity": 74,
                "release_year": 2022,
                "release_date": "2022-01-01",
                "explicit": False,
                "duration_min": 3.1,
            },
        ]
    )
    artists = pd.DataFrame(
        [
            {
                "artist_name": "Divine",
                "time_range": "long_term",
                "rank": 1,
                "genres_str": "desi hip hop",
                "genre_bucket": "Hip-Hop/Rap",
                "region_tag": "India-linked",
                "popularity": 70,
            },
            {
                "artist_name": "Fred again..",
                "time_range": "short_term",
                "rank": 1,
                "genres_str": "house",
                "genre_bucket": "Electronic/Club",
                "region_tag": "International",
                "popularity": 78,
            },
            {
                "artist_name": "Shubh",
                "time_range": "long_term",
                "rank": 2,
                "genres_str": "punjabi hip hop",
                "genre_bucket": "Hip-Hop/Rap",
                "region_tag": "India-linked",
                "popularity": 72,
            },
            {
                "artist_name": "Hanumankind",
                "time_range": "short_term",
                "rank": 5,
                "genres_str": "hip hop",
                "genre_bucket": "Hip-Hop/Rap",
                "region_tag": "India-linked",
                "popularity": 55,
            },
        ]
    )
    recent = pd.DataFrame(
        [
            {
                "track_name": "Big Dawgs",
                "artist_name": "Hanumankind",
                "played_at": "2025-05-10T18:00:00+00:00",
                "popularity": 52,
            },
            {
                "track_name": "Big Dawgs",
                "artist_name": "Hanumankind",
                "played_at": "2025-05-11T18:00:00+00:00",
                "popularity": 52,
            },
            {
                "track_name": "Delilah",
                "artist_name": "Fred again..",
                "played_at": "2025-05-12T19:00:00+00:00",
                "popularity": 78,
            },
        ]
    )
    catalog = build_artist_catalog(artists, tracks, recent)
    return {
        "data_source": "api",
        "user_profile": {"display_name": "Test User", "id": "test_user"},
        "tracks": tracks,
        "artists": catalog,
        "recent": recent,
        "recent_history": recent,
        "saved_tracks": pd.DataFrame(),
        "playlists": pd.DataFrame(),
        "playlist_tracks": {},
        "youtube": pd.DataFrame(),
    }


@pytest.fixture
def sample_bundle(api_fixture_bundle):
    """Backward-compatible alias for tests being migrated."""
    return api_fixture_bundle
