"""Page 10: Role Fit Summary — JD mapped to CV + live listening."""

import streamlit as st

from config import CV_LINKEDIN_URL, CV_PROFILE, DEFAULT_DJ_STORY
from listening_tenure import analyze_listening_tenure, summarize_tenure_for_role_fit
from discovery_engine import (
    build_breakout_watchlist,
    build_daily_listen_timeline,
    build_track_breakout_watchlist,
    format_watchlist_for_display,
    map_role_fit_to_jd,
    watchlist_display_columns,
)
from editorial_engine import analyze_recent_behaviour, generate_india_global_insights, generate_listening_insights
from editorial_engine import score_playlists
from ui.components import data_source_caption, export_buttons, get_session_df, get_session_dict
from ui.theme import page_header
from utils.io import export_markdown


def render():
    cv = CV_PROFILE
    page_header(
        "Role Fit Summary",
        f"{cv['target_role']} — evidence from your listening + verified career history.",
    )

    st.markdown(
        f"**{cv['name']}** · {cv['headline']}  \n"
        f"[LinkedIn profile]({CV_LINKEDIN_URL}) · {cv['contact']}"
    )

    tracks = get_session_df("tracks")
    artists = get_session_df("artists")
    recent = get_session_df("recent")
    if recent.empty:
        recent = get_session_df("recent_history")
    playlist_tracks = get_session_dict("playlist_tracks")

    if tracks.empty and artists.empty:
        st.info(
            "Sidebar → **Data source** → **Re-run full bootstrap** if data is missing."
        )
        return

    data_source_caption()
    saved = get_session_df("saved_tracks")
    watchlist = build_breakout_watchlist(artists, tracks, recent, None, saved, playlist_tracks)
    display_wl = format_watchlist_for_display(watchlist)
    track_watch = build_track_breakout_watchlist(tracks, recent, artists)
    daily = build_daily_listen_timeline(recent)
    insights = generate_listening_insights(tracks, artists)
    india = generate_india_global_insights(artists)
    mood, _ = analyze_recent_behaviour(recent, artists)
    pl_scores = score_playlists(playlist_tracks, artists)
    dj_story = st.session_state.get("dj_story", DEFAULT_DJ_STORY)
    tenure_summary = summarize_tenure_for_role_fit(
        analyze_listening_tenure(tracks, artists, recent, saved)
    )

    md = map_role_fit_to_jd(
        watchlist,
        track_watch,
        daily,
        insights,
        india,
        pl_scores,
        mood,
        dj_story,
        artists,
        tracks,
        tenure_summary=tenure_summary,
        exportify_stats=st.session_state.get("exportify_stats") or {},
        data_source=st.session_state.get("data_source", "api"),
    )

    with st.container(border=True):
        st.markdown(md)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download role fit (Markdown)",
            data=md,
            file_name="editorial_summary.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c2:
        if st.button("Save to outputs/", use_container_width=True):
            path = export_markdown(md)
            st.success(f"Saved to {path}")

    if not display_wl.empty:
        with st.expander("Top breakout artists (quick reference)"):
            cols = watchlist_display_columns(display_wl)
            st.dataframe(display_wl[cols].head(10), use_container_width=True, hide_index=True)

    export_buttons(display_wl.head(20), "role_fit_breakout.csv")
