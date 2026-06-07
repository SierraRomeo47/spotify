"""Tests for data processing helpers."""

import pandas as pd

from data_processing import (
    build_artist_catalog,
    classify_genres,
    convert_duration_ms_to_min,
    empty_data_bundle,
    normalize_tracks,
    calculate_repeat_affinity,
)


def test_classify_genres_hip_hop():
    assert classify_genres(["desi hip hop"]) == "Hip-Hop/Rap"


def test_classify_genres_india():
    assert classify_genres(["punjabi"]) == "India-linked"


def test_classify_genres_electronic():
    assert classify_genres(["house"]) == "Electronic/Club"


def test_convert_duration():
    assert convert_duration_ms_to_min(180000) == 3.0


def test_release_year(api_fixture_bundle):
    from data_processing import calculate_release_year

    assert calculate_release_year("2019-05-17") == 2019


def test_empty_data_bundle():
    bundle = empty_data_bundle()
    assert bundle["data_source"] == "none"
    assert bundle["tracks"].empty
    assert bundle["artists"].empty


def test_normalize_tracks_from_fixture(api_fixture_bundle):
    raw = api_fixture_bundle["tracks"].head(5)
    out = normalize_tracks(raw, source="upload")
    assert "duration_min" in out.columns
    assert len(out) == len(raw)


def test_repeat_affinity(api_fixture_bundle):
    aff = calculate_repeat_affinity(api_fixture_bundle["tracks"])
    assert not aff.empty


def test_build_artist_catalog(api_fixture_bundle):
    cat = build_artist_catalog(
        api_fixture_bundle["artists"],
        api_fixture_bundle["tracks"],
        api_fixture_bundle["recent"],
    )
    assert not cat.empty
    assert "artist_name" in cat.columns
