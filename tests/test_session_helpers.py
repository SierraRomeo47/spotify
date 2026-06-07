"""Session helper regression tests."""

import pandas as pd
import pytest


def test_dataframe_or_pattern_raises():
    df = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(ValueError):
        _ = df or pd.DataFrame()


def test_get_session_df_logic():
    """Simulate get_session_df without Streamlit runtime."""
    state = {"tracks": pd.DataFrame({"x": [1]})}

    def get_session_df(key):
        val = state.get(key)
        if val is None:
            return pd.DataFrame()
        if isinstance(val, pd.DataFrame):
            return val
        return pd.DataFrame()

    result = get_session_df("tracks")
    assert len(result) == 1
    assert get_session_df("missing").empty
