"""Culture & programming lanes — India export and global entry (no genre donuts)."""

import streamlit as st

from discovery_engine import build_breakout_watchlist, format_watchlist_for_display
from ui.components import chart_section, data_source_caption, export_buttons, get_session_df, get_session_dict, missing_data_warning
from ui.theme import page_header
from youtube_processing import extract_music_entries, match_youtube_to_spotify


def _lane_columns(df):
    cols = [
        "artist_name",
        "region",
        "scene",
        "programming_lane",
        "early_discovery_score",
        "editorial_action",
    ]
    return [c for c in cols if c in df.columns]


def render():
    page_header(
        "Culture & programming lanes",
        "Club/electronic discovery in recent rotation + India ↔ global hip-hop in long-term taste — programming tables only.",
    )

    artists = get_session_df("artists")
    tracks = get_session_df("tracks")
    recent = get_session_df("recent")
    if recent.empty:
        recent = get_session_df("recent_history")

    if artists.empty:
        missing_data_warning("artists")
        return

    data_source_caption()
    saved = get_session_df("saved_tracks")
    playlist_tracks = get_session_dict("playlist_tracks")
    india_export = format_watchlist_for_display(
        build_breakout_watchlist(artists, tracks, recent, "india_export", saved, playlist_tracks),
    )
    global_entry = format_watchlist_for_display(
        build_breakout_watchlist(artists, tracks, recent, "global_entry", saved, playlist_tracks),
    )

    col1, col2 = st.columns(2)
    with col1:
        with chart_section("Indian artists — export / diaspora lane"):
            if not india_export.empty:
                st.dataframe(india_export[_lane_columns(india_export)].head(12), hide_index=True, use_container_width=True)
            else:
                st.caption("No India-linked artists in current API data. Fetch Spotify data or adjust filters.")
    with col2:
        with chart_section("International → India entry points"):
            if not global_entry.empty:
                st.dataframe(
                    global_entry[_lane_columns(global_entry)].head(12),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No global-entry lane matches in current API data.")

    yt = st.session_state.get("youtube")
    if yt is not None and hasattr(yt, "empty") and not yt.empty:
        with st.expander("YouTube culture signals (optional upload)"):
            music = extract_music_entries(yt)
            matched, youtube_only = match_youtube_to_spotify(music, artists, tracks)
            if not youtube_only.empty:
                st.caption("YouTube-only leads (not yet in top Spotify rotation)")
                st.dataframe(youtube_only.head(10), hide_index=True, use_container_width=True)
            if not matched.empty:
                st.dataframe(matched.head(8), hide_index=True, use_container_width=True)

    export_buttons(india_export, "india_export_lane.csv")
