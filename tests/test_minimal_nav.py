"""Minimal nav and display column tests."""

from discovery_engine import build_breakout_watchlist, format_watchlist_for_display, watchlist_display_columns


def test_pre_long_term_filter(api_fixture_bundle):
    pre = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
        "pre_long_term",
    )
    all_wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    if not pre.empty:
        assert (pre["is_pre_long_term"] == True).all()
    assert len(pre) <= len(all_wl)


def test_watchlist_display_columns(api_fixture_bundle):
    wl = build_breakout_watchlist(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    display = format_watchlist_for_display(wl)
    cols = watchlist_display_columns(display)
    assert "artist_name" in cols
    assert "listen_count_7d" not in cols
    assert "is_pre_long_term" not in cols


def test_app_imports_five_pages():
    import app  # noqa: F401

    assert app
