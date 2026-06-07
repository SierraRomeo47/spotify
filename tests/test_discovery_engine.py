"""Tests for discovery engine."""

from discovery_engine import (
    build_breakout_watchlist,
    build_daily_listen_timeline,
    enrich_recent_with_dates,
    format_watchlist_for_display,
    has_popularity_data,
    map_role_fit_to_jd,
)
from editorial_engine import generate_listening_insights, score_playlists


def test_enrich_recent_with_dates(api_fixture_bundle):
    recent = enrich_recent_with_dates(api_fixture_bundle["recent"])
    assert "play_date" in recent.columns
    assert not recent.empty


def test_daily_timeline(api_fixture_bundle):
    daily = build_daily_listen_timeline(api_fixture_bundle["recent"])
    assert not daily.empty
    assert "total_plays" in daily.columns


def test_breakout_watchlist_non_empty(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    assert not wl.empty


def test_pre_long_term_higher_discovery(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    assert not wl.empty
    assert (wl["early_discovery_score"] > 0).any()


def test_filter_pre_mainstream(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
        "pre_mainstream",
    )
    assert wl.empty or (wl["popularity_band"] == "Pre-mainstream").all()


def test_map_role_fit_dual_lens(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    md = map_role_fit_to_jd(
        wl,
        __import__("discovery_engine").build_track_breakout_watchlist(
            api_fixture_bundle["tracks"],
            api_fixture_bundle["recent"],
            api_fixture_bundle["artists"],
        ),
        build_daily_listen_timeline(api_fixture_bundle["recent"]),
        generate_listening_insights(api_fixture_bundle["tracks"], api_fixture_bundle["artists"]),
        [],
        score_playlists(api_fixture_bundle["playlist_tracks"], api_fixture_bundle["artists"]),
        "discovery/listening exploration",
        "DJ story",
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
    )
    assert "What I'll do" in md
    assert "ShipWatch" in md
    assert "Sumit Redu" in md
    assert "linkedin.com/in/sumit-redu" in md


def test_has_popularity_data(api_fixture_bundle):
    assert has_popularity_data(api_fixture_bundle["tracks"]) or not has_popularity_data(
        api_fixture_bundle["tracks"]
    )


def test_format_watchlist_display(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    display = format_watchlist_for_display(wl)
    assert "programming_lane" in display.columns
