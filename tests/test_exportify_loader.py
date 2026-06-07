"""Tests for Exportify CSV loading and API merge."""

from pathlib import Path

import pandas as pd

from data_processing import build_artist_catalog
from exportify_loader import (
    build_enrichment_master,
    load_playlist_csv,
    merge_api_with_exportify,
    normalize_exportify_dataframe,
    parse_track_id_from_uri,
)

FIXTURE = Path(__file__).parent / "fixtures" / "exportify_sample.csv"


def test_parse_track_id_from_uri():
    assert parse_track_id_from_uri("spotify:track:abc123") == "abc123"
    assert parse_track_id_from_uri("") == ""


def test_normalize_exportify_dataframe():
    df = pd.read_csv(FIXTURE)
    out = normalize_exportify_dataframe(df, playlist_name="Test")
    assert len(out) == 2
    assert out.iloc[0]["track_id"] == "aaa111"
    assert "desi hip hop" in out.iloc[0]["genres_str"]
    assert out.iloc[0]["popularity"] == 55
    assert out.iloc[1]["danceability"] == 0.75


def test_build_enrichment_master_dedupes():
    df = normalize_exportify_dataframe(pd.read_csv(FIXTURE))
    master = build_enrichment_master(df, df)
    assert len(master) == 2


def test_merge_api_with_exportify_fills_popularity():
    api = pd.DataFrame(
        [
            {
                "track_id": "aaa111",
                "track_name": "Test Track One",
                "artist_name": "Divine",
                "popularity": None,
                "genres_str": "",
            }
        ]
    )
    master = normalize_exportify_dataframe(pd.read_csv(FIXTURE))
    merged = merge_api_with_exportify(api, master)
    assert merged.iloc[0]["popularity"] == 55
    assert "desi hip hop" in str(merged.iloc[0]["genres_str"])


def test_build_artist_catalog_from_exportify_genres():
    master = normalize_exportify_dataframe(pd.read_csv(FIXTURE))
    catalog = build_artist_catalog(
        pd.DataFrame(),
        master,
        pd.DataFrame(),
        None,
        None,
    )
    divine = catalog[catalog["artist_name"] == "Divine"]
    assert not divine.empty
    assert divine.iloc[0]["genre_bucket"] == "Hip-Hop/Rap"
    fred = catalog[catalog["artist_name"] == "Fred again.."]
    assert fred.iloc[0]["scene_tag"] != ""


def test_load_playlist_csv_fixture():
    out = load_playlist_csv(FIXTURE)
    assert not out.empty
    assert "track_name" in out.columns
