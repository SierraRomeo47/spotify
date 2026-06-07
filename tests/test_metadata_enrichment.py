"""Tests for optional metadata enrichment (mocked HTTP)."""

from unittest.mock import patch

import pandas as pd

from metadata_enrichment import enrich_sparse_artists, enrich_artist_tags


@patch("metadata_enrichment.fetch_musicbrainz_artist_tags", return_value=["hip hop", "rap"])
@patch("metadata_enrichment.fetch_lastfm_artist_tags", return_value=[])
def test_enrich_sparse_artists(_lfm, _mb):
    catalog = pd.DataFrame(
        [
            {"artist_name": "Unknown Artist", "genres_str": "", "genre_bucket": "", "region_tag": ""},
        ]
    )
    out, msg = enrich_sparse_artists(catalog, max_artists=5)
    assert "Enriched 1" in msg
    assert out.iloc[0]["genre_bucket"] == "Hip-Hop/Rap"


@patch("metadata_enrichment.fetch_musicbrainz_artist_tags", return_value=["house"])
@patch("metadata_enrichment.fetch_lastfm_artist_tags", return_value=[])
def test_enrich_artist_tags_prefers_musicbrainz(_lfm, _mb):
    tags, src = enrich_artist_tags("Test DJ")
    assert tags == ["house"]
    assert src == "musicbrainz"
