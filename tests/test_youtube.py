"""YouTube processing tests."""

import pandas as pd

from youtube_processing import extract_music_entries, match_youtube_to_spotify, normalize_youtube_history


def test_extract_music_entries():
    df = pd.DataFrame(
        [
            {"title": "Divine - Mirchi (Official Video)", "channel": "DivineVEVO", "manual_artist": "Divine"},
            {"title": "How to cook pasta", "channel": "Food Channel", "manual_artist": ""},
        ]
    )
    music = extract_music_entries(df)
    assert len(music) == 1


def test_match_youtube_to_spotify(sample_bundle):
    yt = pd.DataFrame(
        [
            {
                "title": "JID - Surround Sound",
                "channel": "JID",
                "manual_artist": "JID",
                "url": "",
                "watched_at": "",
            }
        ]
    )
    matched = match_youtube_to_spotify(yt, sample_bundle["artists"], sample_bundle["tracks"])
    assert "overlap" in matched.columns
