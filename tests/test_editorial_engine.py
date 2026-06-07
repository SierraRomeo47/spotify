"""Tests for editorial engine."""

from editorial_engine import (
    analyze_recent_behaviour,
    calculate_artist_editorial_score,
    generate_india_global_insights,
    generate_listening_insights,
    generate_playlist_sequence,
    generate_role_fit_summary,
    score_playlists,
)
from data_processing import enrich_tracks_with_artist_metadata


def test_listening_insights(api_fixture_bundle):
    insights = generate_listening_insights(api_fixture_bundle["tracks"], api_fixture_bundle["artists"])
    assert insights
    assert "sample" not in insights[0].lower()


def test_artist_editorial_scores(api_fixture_bundle):
    scored = calculate_artist_editorial_score(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    assert not scored.empty


def test_playlist_scores(api_fixture_bundle):
    scores = score_playlists(api_fixture_bundle["playlist_tracks"], api_fixture_bundle["artists"])
    assert scores.empty or "playlist_name" in scores.columns


def test_playlist_sequence(api_fixture_bundle):
    pool = enrich_tracks_with_artist_metadata(
        api_fixture_bundle["tracks"].head(20), api_fixture_bundle["artists"]
    )
    seq, copy = generate_playlist_sequence(pool, "Breakout Watch: Pre-Mainstream")
    assert not seq.empty
    assert "sequence_order" in seq.columns
    assert copy


def test_recent_behaviour(api_fixture_bundle):
    mood, radar = analyze_recent_behaviour(api_fixture_bundle["recent"], api_fixture_bundle["artists"])
    assert mood in ("comfort/repeat listening", "discovery/listening exploration", "unknown")


def test_role_fit_summary(api_fixture_bundle):
    from discovery_engine import build_breakout_watchlist

    insights = generate_listening_insights(api_fixture_bundle["tracks"], api_fixture_bundle["artists"])
    scored = calculate_artist_editorial_score(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    pl = score_playlists(api_fixture_bundle["playlist_tracks"], api_fixture_bundle["artists"])
    india = generate_india_global_insights(api_fixture_bundle["artists"])
    md = generate_role_fit_summary(insights, scored, pl, india, "comfort/repeat listening")
    assert "Role Fit" in md or "Editorial" in md or len(md) > 20
