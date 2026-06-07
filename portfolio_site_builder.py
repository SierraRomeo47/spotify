"""Build static portfolio JSON for Vercel (headless — no Streamlit)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    CV_PROFILE,
    DEFAULT_DJ_STORY,
    DISCLAIMER,
    EDITORIAL_CONCEPTS,
    PROFILE_ROLE_PILLS,
    ROLE_WORKFLOW,
)
from data_processing import (
    enrich_tracks_with_artist_metadata,
)
from discovery_engine import (
    build_breakout_watchlist,
    build_daily_listen_timeline,
    build_track_breakout_watchlist,
    discovery_summary_metrics,
    format_watchlist_for_display,
    map_role_fit_to_jd,
    track_watchlist_display_columns,
    watchlist_display_columns,
)
from editorial_engine import (
    analyze_recent_behaviour,
    generate_listening_insights,
    generate_playlist_sequence,
    generate_india_global_insights,
    score_playlists,
)
from exportify_loader import summarize_audio_profile
from employer_display import (
    filter_records,
    long_term_track_columns,
    sequence_track_columns,
)
from library_loader import load_local_library_bundle
from listening_tenure import analyze_listening_tenure, summarize_tenure_for_role_fit
from utils.charts import bar_chart_simple


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value


def df_to_records(df: pd.DataFrame | None, limit: int | None = None) -> list[dict]:
    if df is None or df.empty:
        return []
    subset = df.head(limit) if limit else df
    records = json.loads(subset.to_json(orient="records", date_format="iso"))
    return records


def fig_to_dict(fig) -> dict | None:
    if fig is None:
        return None
    try:
        return json.loads(fig.to_json())
    except Exception:
        return None


def load_headless_dataset() -> dict[str, Any]:
    """Load my_spotify_data + optional Exportify enrichment + API exports."""
    return load_local_library_bundle()


def build_portfolio_site_payload(dj_story: str | None = None) -> dict[str, Any]:
    """Assemble full JSON document for Next.js."""
    data = load_headless_dataset()
    tracks = data["tracks"]
    artists = data["artists"]
    recent = data["recent"]
    saved = data["saved_tracks"]
    playlist_tracks = data["playlist_tracks"]
    master = data["exportify_master"]

    watchlist = build_breakout_watchlist(artists, tracks, recent, None, saved, playlist_tracks)
    display_wl = format_watchlist_for_display(watchlist)
    wl_cols = watchlist_display_columns(display_wl)
    watchlist_records = df_to_records(display_wl[wl_cols] if wl_cols else display_wl, limit=80)

    india_export = format_watchlist_for_display(
        build_breakout_watchlist(artists, tracks, recent, "india_export", saved, playlist_tracks)
    )
    global_entry = format_watchlist_for_display(
        build_breakout_watchlist(artists, tracks, recent, "global_entry", saved, playlist_tracks)
    )
    lane_cols = [
        "artist_name",
        "region",
        "scene",
        "programming_lane",
        "early_discovery_score",
        "editorial_action",
    ]

    track_watch = build_track_breakout_watchlist(tracks, recent, artists)
    tw_cols = track_watchlist_display_columns(track_watch)
    daily = build_daily_listen_timeline(recent)
    metrics = discovery_summary_metrics(watchlist, recent)

    daily_sorted = daily.sort_values("play_date") if not daily.empty else daily
    chart_daily = None
    if not daily_sorted.empty:
        chart_daily = fig_to_dict(
            bar_chart_simple(
                daily_sorted["play_date"].astype(str),
                daily_sorted["total_plays"],
                x_title="Date",
                y_title="Plays",
            )
        )

    audio_df = master if not master.empty else saved
    if audio_df.empty and not tracks.empty:
        audio_df = tracks
    audio_profile = summarize_audio_profile(audio_df) or {}

    insights = generate_listening_insights(tracks, artists)
    india_insights = generate_india_global_insights(artists)
    mood, _ = analyze_recent_behaviour(recent, artists)
    pl_scores = score_playlists(playlist_tracks, artists)
    tenure = analyze_listening_tenure(tracks, artists, recent, saved)
    tenure_summary = summarize_tenure_for_role_fit(tenure)

    role_md = map_role_fit_to_jd(
        watchlist,
        track_watch,
        daily,
        insights,
        india_insights,
        pl_scores,
        mood,
        dj_story or DEFAULT_DJ_STORY,
        artists,
        tracks,
        tenure_summary=tenure_summary,
        exportify_stats=data.get("exportify_stats") or {},
        data_source=data.get("data_source", "exportify"),
    )

    score_cols = [
        c
        for c in [
            "playlist_name",
            "cohesion_score",
            "discovery_score",
            "recency_score",
            "india_global_bridge_score",
            "track_count",
        ]
        if c in pl_scores.columns
    ]
    sort_col = "discovery_score" if "discovery_score" in pl_scores.columns else "cohesion_score"
    ranked_scores = (
        pl_scores.sort_values(sort_col, ascending=False) if not pl_scores.empty and sort_col in pl_scores.columns else pl_scores
    )

    long_t = tenure.get("long_term_tracks")
    if long_t is None:
        long_t = pd.DataFrame()
    lt_cols = long_term_track_columns(long_t) if not long_t.empty else []
    if not long_t.empty and lt_cols:
        long_t_export = long_t.sort_values("rank") if "rank" in long_t.columns else long_t
        long_t_records = filter_records(df_to_records(long_t_export[lt_cols], limit=50), lt_cols)
    else:
        long_t_records = []

    seq_cols = sequence_track_columns()
    sequences: dict[str, Any] = {}
    pool = tracks if not tracks.empty else saved
    if pool is not None and not pool.empty:
        pool = enrich_tracks_with_artist_metadata(pool, artists)
    for concept in EDITORIAL_CONCEPTS[:3]:
        if pool is not None and not pool.empty:
            seq_df, copy = generate_playlist_sequence(pool, concept)
            seq_export = seq_df[seq_cols] if not seq_df.empty else seq_df
            sequences[concept] = {
                "narrative": copy,
                "tracks": filter_records(df_to_records(seq_export, limit=20), seq_cols),
            }
        else:
            sequences[concept] = {"narrative": "No tracks available.", "tracks": []}

    built_at = datetime.now(timezone.utc).isoformat()

    return {
        "meta": {
            "built_at": built_at,
            "data_source": data.get("data_source", "exportify"),
            "exportify_stats": data.get("exportify_stats", {}),
            "disclaimer": DISCLAIMER,
            "role_workflow": ROLE_WORKFLOW,
        },
        "home": {
            "dj_story": dj_story or DEFAULT_DJ_STORY,
            "cv": CV_PROFILE,
            "role_pills": PROFILE_ROLE_PILLS,
            "intro_markdown": (
                "I am applying for **Editor, Music & Culture (International & Hip-Hop)** in Mumbai. "
                "This site is a working portfolio — not a dashboard demo — built from my own listening "
                "history and editorial judgment.\n\n"
                "Recent rotation leans club and electronic; long-term taste runs through India-linked "
                "hip-hop and global crossovers. Each section shows how I would spot momentum, programme "
                "lanes, and sequence a set with a point of view."
            ),
        },
        "role_fit": {
            "markdown": role_md,
            "breakout_preview": watchlist_records[:10],
        },
        "discovery": {
            "metrics": metrics,
            "watchlist_all": watchlist_records,
            "daily_plays": df_to_records(
                daily[
                    ["play_date", "total_plays", "unique_artists", "new_artists", "top_artist_that_day"]
                ]
                if not daily.empty
                else daily
            ),
            "track_watchlist": df_to_records(track_watch[tw_cols] if tw_cols else track_watch, limit=15),
            "chart_daily": chart_daily,
            "audio_profile": audio_profile,
        },
        "culture": {
            "india_export": df_to_records(
                india_export[[c for c in lane_cols if c in india_export.columns]].head(12)
                if not india_export.empty
                else india_export
            ),
            "global_entry": df_to_records(
                global_entry[[c for c in lane_cols if c in global_entry.columns]].head(12)
                if not global_entry.empty
                else global_entry
            ),
        },
        "curate": {
            "tenure": {
                "metrics": tenure.get("metrics", {}),
                "narrative": tenure.get("narrative", ""),
                "genre_divisions": df_to_records(tenure.get("genre_divisions")),
                "region_divisions": df_to_records(tenure.get("region_divisions")),
                "scene_divisions": df_to_records(tenure.get("scene_divisions")),
                "long_term_tracks": long_t_records,
                "long_term_track_columns": lt_cols,
            },
            "playlist_scores": df_to_records(ranked_scores[score_cols] if score_cols else ranked_scores, limit=25),
            "sequences": sequences,
        },
    }


def write_portfolio_json(path: Path | None = None) -> Path:
    path = path or Path(__file__).resolve().parent / "web" / "public" / "data" / "portfolio.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_portfolio_site_payload()
    path.write_text(json.dumps(payload, indent=2, default=_json_safe), encoding="utf-8")
    return path
