"""Tests for auto_enrich_catalog prioritization."""

import pandas as pd

from metadata_enrichment import auto_enrich_catalog
from unittest.mock import patch


@patch("metadata_enrichment.enrich_sparse_artists")
def test_auto_enrich_prioritizes_best_rank(mock_enrich):
    catalog = pd.DataFrame(
        [
            {"artist_name": "Low Priority", "genres_str": "", "best_rank": 500},
            {"artist_name": "High Priority", "genres_str": "", "best_rank": 1},
        ]
    )
    mock_enrich.return_value = (catalog, "ok")

    auto_enrich_catalog(catalog)

    called_df = mock_enrich.call_args[0][0]
    assert called_df.iloc[0]["artist_name"] == "High Priority"
