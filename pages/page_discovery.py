"""Discovery — breakout watchlist and plays per day (employer-focused)."""

import streamlit as st

from discovery_engine import (
    build_breakout_watchlist,
    build_daily_listen_timeline,
    build_track_breakout_watchlist,
    discovery_summary_metrics,
    format_watchlist_for_display,
    track_watchlist_display_columns,
    watchlist_display_columns,
)
from exportify_loader import summarize_audio_profile
from ui.components import chart_section, data_source_caption, export_buttons, get_session_df, get_session_dict, missing_data_warning
from ui.theme import page_header
from utils.charts import bar_chart_simple
from utils.io import export_csv


def render():
    page_header(
        "Discovery",
        "Artists you're leaning into before they become long-term staples — from your Spotify listening, not chart data.",
    )

    artists = get_session_df("artists")
    tracks = get_session_df("tracks")
    recent = get_session_df("recent")
    if recent.empty:
        recent = get_session_df("recent_history")
    saved = get_session_df("saved_tracks")
    playlist_tracks = get_session_dict("playlist_tracks")

    master = get_session_df("exportify_master")
    if artists.empty and recent.empty and tracks.empty and master.empty:
        missing_data_warning("listening data")
        return

    data_source_caption()
    st.caption(
        "Spotify returns up to 50 recent plays per fetch; re-fetch after listening sessions for a richer window."
    )

    filter_mode = st.selectbox(
        "Show",
        ["All artists", "Hip-hop & indie (catalog)", "Pre-long-term only"],
        label_visibility="collapsed",
    )
    filter_lane = {
        "Pre-long-term only": "pre_long_term",
        "Hip-hop & indie (catalog)": "hiphop_indie",
    }.get(filter_mode)

    watchlist = build_breakout_watchlist(
        artists, tracks, recent, filter_lane, saved, playlist_tracks
    )
    track_watch = build_track_breakout_watchlist(tracks, recent, artists)
    daily = build_daily_listen_timeline(recent)
    metrics = discovery_summary_metrics(watchlist, recent)

    c1, c2 = st.columns(2)
    c1.metric("Pre-long-term artists", metrics["new_artists_pre_long_term"])
    c2.metric("Artists in window", metrics["unique_artists_in_window"])

    if not watchlist.empty:
        with chart_section("Breakout artist watchlist"):
            display_wl = format_watchlist_for_display(watchlist)
            cols = watchlist_display_columns(display_wl)
            st.dataframe(display_wl[cols].head(30), use_container_width=True, hide_index=True)
            if st.button("Export breakout watchlist to outputs/", key="exp_breakout"):
                export_csv(display_wl, "breakout_watchlist_export.csv")
                st.success("Saved to outputs/breakout_watchlist_export.csv")
    else:
        st.info("No watchlist rows for this filter. Try **All artists** or fetch more recent plays.")

    if not daily.empty:
        daily_sorted = daily.sort_values("play_date")
        with chart_section("Plays per day"):
            fig = bar_chart_simple(
                daily_sorted["play_date"].astype(str),
                daily_sorted["total_plays"],
                x_title="Date",
                y_title="Plays",
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Daily log & track watchlist"):
        if not daily.empty:
            st.dataframe(
                daily[
                    ["play_date", "total_plays", "unique_artists", "new_artists", "top_artist_that_day"]
                ],
                use_container_width=True,
                hide_index=True,
            )
        if not track_watch.empty:
            tw_cols = track_watchlist_display_columns(track_watch)
            st.dataframe(track_watch[tw_cols].head(10), use_container_width=True, hide_index=True)

    audio_df = master if not master.empty else saved
    if audio_df.empty and not tracks.empty:
        audio_df = tracks
    profile = summarize_audio_profile(audio_df)
    if profile:
        with st.expander("Audio profile (Exportify — tempo / energy / valence)"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Median tempo", profile.get("median_tempo", "—"))
            c2.metric("Median energy", profile.get("median_energy", "—"))
            c3.metric("Median danceability", profile.get("median_danceability", "—"))
            c4.metric("Tracks sampled", profile.get("track_count", 0))

    export_buttons(watchlist.head(20), "breakout_artists.csv")
