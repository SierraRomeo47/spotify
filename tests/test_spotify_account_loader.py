"""Tests for Spotify privacy export loader (my_spotify_data)."""

import json
from pathlib import Path

import pytest

from spotify_account_loader import (
    account_data_available,
    derive_top_tracks_from_streaming,
    load_spotify_account_bundle,
    load_streaming_history,
    load_your_library,
)


@pytest.fixture
def account_dir(tmp_path, monkeypatch):
    root = tmp_path / "Spotify Account Data"
    root.mkdir(parents=True)

    streaming = [
        {
            "endTime": "2025-06-01 12:00",
            "artistName": "Artist A",
            "trackName": "Track One",
            "msPlayed": 180000,
        },
        {
            "endTime": "2025-06-02 12:00",
            "artistName": "Artist B",
            "trackName": "Track Two",
            "msPlayed": 200000,
        },
    ]
    (root / "StreamingHistory_music_0.json").write_text(json.dumps(streaming), encoding="utf-8")

    library = {
        "tracks": [
            {
                "artist": "Artist A",
                "album": "Album",
                "track": "Track One",
                "uri": "spotify:track:abc123",
            }
        ]
    }
    (root / "YourLibrary.json").write_text(json.dumps(library), encoding="utf-8")

    playlists = {
        "playlists": [
            {
                "name": "Test Mix",
                "items": [
                    {
                        "addedDate": "2025-06-01",
                        "track": {
                            "trackName": "Track Two",
                            "artistName": "Artist B",
                            "albumName": "Album B",
                            "trackUri": "spotify:track:def456",
                        },
                    }
                ],
            }
        ]
    }
    (root / "Playlist1.json").write_text(json.dumps(playlists), encoding="utf-8")

    monkeypatch.setattr("spotify_account_loader.SPOTIFY_ACCOUNT_DATA_DIR", root)
    from spotify_account_loader import clear_account_bundle_cache

    clear_account_bundle_cache()
    return root


def test_account_data_available(account_dir):
    assert account_data_available(account_dir) is True


def test_load_streaming_history(account_dir):
    df = load_streaming_history(account_dir)
    assert len(df) == 2
    assert "played_at" in df.columns


def test_load_your_library(account_dir):
    df = load_your_library(account_dir)
    assert len(df) == 1
    assert df.iloc[0]["track_id"] == "abc123"


def test_account_bundle_stats(account_dir):
    bundle = load_spotify_account_bundle(account_dir)
    assert bundle["stats"]["streaming_plays"] == 2
    assert bundle["stats"]["liked_tracks"] == 1
    assert len(bundle["playlist_tracks"]) == 1
    assert not bundle["tracks"].empty
    assert not bundle["recent"].empty


def test_derive_top_tracks_has_time_ranges(account_dir):
    streaming = load_streaming_history(account_dir)
    top = derive_top_tracks_from_streaming(streaming)
    assert "time_range" in top.columns
    assert set(top["time_range"].unique()) <= {"short_term", "medium_term", "long_term"}
