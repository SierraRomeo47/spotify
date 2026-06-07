"""Curate — listening tenure (API), playlist proof, playlist scores."""

from datetime import datetime

import streamlit as st

from config import EDITORIAL_CONCEPTS, SPOTIFY_MEMBER_SINCE_YEAR
from data_processing import enrich_tracks_with_artist_metadata
from editorial_engine import generate_playlist_sequence, score_playlists
from listening_tenure import analyze_listening_tenure
from ui.components import chart_section, data_source_caption, export_buttons, get_session_df, get_session_dict, has_listening_data, missing_data_warning
from ui.theme import page_header
from utils.io import export_csv


def _render_builder():
    tracks = get_session_df("tracks")
    recent = get_session_df("recent")
    if recent.empty:
        recent = get_session_df("recent_history")
    saved = get_session_df("saved_tracks")
    playlist_tracks = get_session_dict("playlist_tracks")
    artists = get_session_df("artists")

    c1, c2 = st.columns(2)
    with c1:
        source = st.selectbox(
            "Source",
            ["Top tracks", "Recently played", "Saved tracks", "Selected playlist"],
            key="curate_src",
        )
    with c2:
        concept = st.selectbox("Editorial concept", EDITORIAL_CONCEPTS, key="curate_concept")

    pool = tracks
    if source == "Recently played" and not recent.empty:
        pool = recent.copy()
        if "rank" not in pool.columns:
            pool["rank"] = range(1, len(pool) + 1)
    elif source == "Saved tracks" and not saved.empty:
        pool = saved
    elif source == "Selected playlist" and playlist_tracks:
        pl_map = {
            (v["playlist_name"].iloc[0] if "playlist_name" in v.columns else k): k
            for k, v in playlist_tracks.items()
        }
        choice = st.selectbox("Playlist", list(pl_map.keys()), key="curate_pl")
        pool = playlist_tracks[pl_map[choice]]

    if pool is None or pool.empty:
        missing_data_warning("tracks for selected source")
        return

    pool = enrich_tracks_with_artist_metadata(pool, artists)
    seq_df, copy = generate_playlist_sequence(pool, concept)

    with chart_section("Editorial narrative"):
        st.markdown(copy)
    with chart_section("Sequence"):
        st.dataframe(seq_df, use_container_width=True, hide_index=True)
    export_buttons(seq_df, "playlist_sequence.csv")


def _render_listening_tenure():
    tracks = get_session_df("tracks")
    artists = get_session_df("artists")
    recent = get_session_df("recent")
    if recent.empty:
        recent = get_session_df("recent_history")
    saved = get_session_df("saved_tracks")

    analysis = analyze_listening_tenure(tracks, artists, recent, saved)
    m = analysis["metrics"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Years on Spotify", f"~{m['years_on_spotify']}")
    c2.metric("Unique songs (merged)", m["unique_songs_merged"])
    c3.metric("Artists (catalog)", m["unique_artists_catalog"])
    c4.metric("All-time top tracks", m["long_term_track_count"])

    with chart_section("Listening profile"):
        st.markdown(analysis.get("narrative", ""))

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Artist divisions — genre**")
        genre = analysis["genre_divisions"]
        if not genre.empty:
            st.bar_chart(genre.set_index("division"))
    with col_b:
        st.markdown("**Artist divisions — region / market**")
        region = analysis["region_divisions"]
        if not region.empty:
            st.bar_chart(region.set_index("division"))

    scene = analysis["scene_divisions"]
    if not scene.empty:
        with st.expander("Artist divisions — scene / lane"):
            st.bar_chart(scene.set_index("division"))

    long_t = analysis["long_term_tracks"]
    if not long_t.empty:
        display_cols = [
            c
            for c in [
                "rank",
                "track_name",
                "artist_name",
                "genre_bucket",
                "region_tag",
                "scene_tag",
                "release_year",
            ]
            if c in long_t.columns
        ]
        with chart_section("All-time top tracks"):
            st.dataframe(
                long_t.sort_values("rank")[display_cols] if "rank" in long_t.columns else long_t[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        export_buttons(long_t, "all_time_top_tracks_api.csv")

    union = analysis["union_tracks"]
    if not union.empty:
        with st.expander("All unique songs across API windows"):
            cols = [c for c in ["track_name", "artist_name", "genre_bucket", "region_tag"] if c in union.columns]
            st.dataframe(union[cols], use_container_width=True, hide_index=True)
            export_buttons(union, "merged_songs_api.csv")


def _render_playlist_scores():
    playlists = get_session_df("playlists")
    playlist_tracks = get_session_dict("playlist_tracks")
    artists = get_session_df("artists")

    if playlists.empty or not playlist_tracks:
        missing_data_warning("playlists")
        return

    scores = score_playlists(playlist_tracks, artists)
    if scores.empty:
        st.warning("Could not score playlists.")
        return

    export_csv(scores, "playlist_strategy_export.csv")
    display_cols = [
        c
        for c in [
            "playlist_name",
            "cohesion_score",
            "discovery_score",
            "recency_score",
            "india_global_bridge_score",
            "track_count",
        ]
        if c in scores.columns
    ]
    sort_col = "discovery_score" if "discovery_score" in scores.columns else "cohesion_score"
    if sort_col in scores.columns:
        ranked = scores.sort_values(sort_col, ascending=False)
    else:
        ranked = scores
    st.dataframe(ranked[display_cols].head(10), use_container_width=True, hide_index=True)
    with st.expander(f"All playlists ({len(scores)})"):
        st.dataframe(
            ranked[display_cols],
            use_container_width=True,
            hide_index=True,
            height=min(400, 35 * len(scores) + 38),
        )


def render():
    page_header("Curate", "Listening profile, playlist sequencing, and scores.")

    if not has_listening_data():
        missing_data_warning("listening data")
        return

    data_source_caption()

    tab_tenure, tab_proof, tab_scores = st.tabs(
        [
            f"Listening tenure (~{datetime.now().year - SPOTIFY_MEMBER_SINCE_YEAR} yrs)",
            "Playlist proof",
            "Your playlists (top 3)",
        ]
    )
    with tab_tenure:
        _render_listening_tenure()
    with tab_proof:
        _render_builder()
    with tab_scores:
        _render_playlist_scores()
