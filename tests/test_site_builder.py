"""Tests for Vercel portfolio JSON builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_site_builder import build_portfolio_site_payload, write_portfolio_json


@pytest.fixture
def exportify_dir(tmp_path, monkeypatch):
    """Minimal Exportify CSV for headless build."""
    playlists = tmp_path / "spotify_playlists"
    playlists.mkdir()
    csv = playlists / "sample.csv"
    csv.write_text(
        "Track URI,Track Name,Album Name,Artist Name(s),Release Date,Genres,Popularity,"
        "Danceability,Energy,Tempo,Valence\n"
        'spotify:track:1,Test Track,Album,Artist One,2024-01-01,"hip hop; rap",'
        "35,0.7,0.8,120,0.5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "exportify_loader.EXPORTIFY_PLAYLISTS_DIR",
        playlists,
    )
    monkeypatch.setattr(
        "library_loader.EXPORTIFY_PLAYLISTS_DIR",
        playlists,
    )
    monkeypatch.setattr(
        "spotify_account_loader.SPOTIFY_ACCOUNT_DATA_DIR",
        tmp_path / "missing_account_data",
    )
    from exportify_loader import clear_exportify_bundle_cache
    from spotify_account_loader import clear_account_bundle_cache

    clear_exportify_bundle_cache()
    clear_account_bundle_cache()
    return playlists


def test_build_portfolio_payload_structure(exportify_dir):
    payload = build_portfolio_site_payload()
    assert "meta" in payload
    assert "home" in payload
    assert "role_fit" in payload
    assert "discovery" in payload
    assert "culture" in payload
    assert "curate" in payload
    assert payload["meta"]["built_at"]
    assert payload["meta"]["data_source"] in (
        "exportify",
        "api+exportify",
        "api",
        "account",
        "account+exportify",
        "account+api",
        "account+exportify+api",
    )
    assert isinstance(payload["discovery"]["watchlist_all"], list)
    assert isinstance(payload["curate"]["playlist_scores"], list)
    assert isinstance(payload["curate"]["sequences"], dict)


def test_role_fit_markdown_non_empty(exportify_dir):
    payload = build_portfolio_site_payload()
    md = payload["role_fit"]["markdown"]
    assert isinstance(md, str)
    assert len(md) > 100
    assert "Role Fit" in md or "Sumit" in md


def test_write_portfolio_json(tmp_path, exportify_dir):
    out = tmp_path / "portfolio.json"
    path = write_portfolio_json(out)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["meta"]["disclaimer"]
