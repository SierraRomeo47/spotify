"""Tests for API-only listening tenure analysis."""

from listening_tenure import analyze_listening_tenure, summarize_tenure_for_role_fit
from config import SPOTIFY_MEMBER_SINCE_YEAR


def test_analyze_listening_tenure_from_api_fixture(api_fixture_bundle):
    analysis = analyze_listening_tenure(
        api_fixture_bundle["tracks"],
        api_fixture_bundle["artists"],
        api_fixture_bundle["recent"],
        api_fixture_bundle.get("saved_tracks"),
    )
    m = analysis["metrics"]
    assert m["years_on_spotify"] >= 8
    assert m["unique_songs_merged"] > 0
    assert m["long_term_track_count"] > 0
    assert not analysis["long_term_tracks"].empty


def test_summarize_tenure_for_role_fit(api_fixture_bundle):
    analysis = analyze_listening_tenure(
        api_fixture_bundle["tracks"],
        api_fixture_bundle["artists"],
        api_fixture_bundle["recent"],
    )
    s = summarize_tenure_for_role_fit(analysis)
    assert str(SPOTIFY_MEMBER_SINCE_YEAR) in s
    assert "unique songs" in s
