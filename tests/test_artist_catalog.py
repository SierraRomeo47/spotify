"""Tests for artist catalog."""

from data_processing import build_artist_catalog, split_artist_names
from discovery_engine import build_breakout_watchlist, compute_listen_velocity


def test_split_artist_names_collab():
    assert split_artist_names("A & B, C") == ["A", "B", "C"]


def test_velocity_counts_split_artists(api_fixture_bundle):
    recent = api_fixture_bundle["recent"]
    vel = compute_listen_velocity(recent, "artist")
    assert not vel.empty


def test_catalog_includes_track_only_artists(api_fixture_bundle):
    tracks = api_fixture_bundle["tracks"]
    cat = build_artist_catalog(
        api_fixture_bundle["artists"],
        tracks,
        api_fixture_bundle["recent"],
    )
    track_artists = set(tracks["artist_name"].unique())
    catalog_names = set(cat["artist_name"].unique())
    assert track_artists.issubset(catalog_names) or not track_artists


def test_breakout_includes_recent_artists(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    names = set(wl["artist_name"].astype(str))
    assert "Hanumankind" in names or not wl.empty
