"""Tests for auto bootstrap step ordering."""

from session_state import run_bootstrap_steps


def test_run_bootstrap_steps_full():
    steps = run_bootstrap_steps(
        exportify_available=True,
        spotify_credentials=True,
        spotify_cache_exists=True,
        auto_enrich=True,
    )
    assert steps == ["exportify:load", "spotify:fetch", "enrich:genres"]


def test_run_bootstrap_steps_exportify_only():
    steps = run_bootstrap_steps(
        exportify_available=True,
        spotify_credentials=False,
        spotify_cache_exists=False,
        auto_enrich=False,
    )
    assert steps == ["exportify:load"]


def test_run_bootstrap_steps_no_exportify():
    steps = run_bootstrap_steps(
        exportify_available=False,
        spotify_credentials=True,
        spotify_cache_exists=False,
        auto_enrich=True,
    )
    assert steps == ["spotify:fetch", "enrich:genres"]
