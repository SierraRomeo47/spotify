"""API-only listening tenure (~9 years on Spotify) — artists, divisions, songs heard."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from config import SPOTIFY_MEMBER_SINCE_YEAR, TIME_RANGE_LABELS
from data_processing import (
    enrich_tracks_with_artist_metadata,
    format_tag_label,
)


def _track_key(track_name: str, artist_name: str) -> tuple[str, str]:
    from data_processing import _norm_name

    return _norm_name(track_name), _norm_name(artist_name)


def _union_tracks(*frames: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate tracks by normalized track + artist across API sources."""
    rows: dict[tuple[str, str], dict] = {}
    for df in frames:
        if df is None or df.empty or "track_name" not in df.columns:
            continue
        for _, r in df.iterrows():
            key = _track_key(r.get("track_name", ""), r.get("artist_name", ""))
            if not key[0]:
                continue
            rows[key] = r.to_dict()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows.values())


def _tracks_for_range(tracks_df: pd.DataFrame, time_range: str) -> pd.DataFrame:
    if tracks_df.empty or "time_range" not in tracks_df.columns:
        return pd.DataFrame()
    return tracks_df[tracks_df["time_range"] == time_range].copy()


def _division_counts(series: pd.Series) -> pd.DataFrame:
    cleaned = series.replace("", pd.NA).dropna().astype(str).str.strip()
    cleaned = cleaned[cleaned != ""]
    if cleaned.empty:
        return pd.DataFrame(columns=["division", "count"])
    counts = cleaned.value_counts().reset_index()
    counts.columns = ["division", "count"]
    counts["division"] = counts["division"].map(format_tag_label)
    return counts


def analyze_listening_tenure(
    tracks_df: pd.DataFrame,
    artists_df: pd.DataFrame,
    recent_df: pd.DataFrame,
    saved_tracks_df: pd.DataFrame | None = None,
    member_since_year: int = SPOTIFY_MEMBER_SINCE_YEAR,
) -> dict:
    """
    Build Curate / Role Fit evidence from Spotify Web API data only.
    Lifetime play counts are not available via API; long_term top tracks proxy all-time taste.
    """
    saved = saved_tracks_df if saved_tracks_df is not None else pd.DataFrame()
    now_year = datetime.now().year
    years_on_spotify = max(0, now_year - member_since_year)

    long_t = _tracks_for_range(tracks_df, "long_term")
    med_t = _tracks_for_range(tracks_df, "medium_term")
    short_t = _tracks_for_range(tracks_df, "short_term")

    union = _union_tracks(long_t, med_t, short_t, saved, recent_df)
    if not union.empty:
        union = enrich_tracks_with_artist_metadata(union, artists_df)

    long_enriched = enrich_tracks_with_artist_metadata(long_t, artists_df) if not long_t.empty else long_t
    med_enriched = enrich_tracks_with_artist_metadata(med_t, artists_df) if not med_t.empty else med_t

    unique_songs = len(union)
    unique_artists_catalog = (
        int(artists_df["artist_name"].nunique()) if not artists_df.empty else 0
    )
    unique_artists_in_tracks = (
        int(union["artist_name"].nunique()) if not union.empty and "artist_name" in union.columns else 0
    )

    genre_div = _division_counts(artists_df.get("genre_bucket", pd.Series(dtype=str)))
    region_div = _division_counts(artists_df.get("region_tag", pd.Series(dtype=str)))
    scene_div = _division_counts(artists_df.get("scene_tag", pd.Series(dtype=str)))

    metrics = {
        "member_since_year": member_since_year,
        "years_on_spotify": years_on_spotify,
        "unique_songs_merged": unique_songs,
        "unique_artists_catalog": unique_artists_catalog,
        "unique_artists_in_tracks": unique_artists_in_tracks,
        "long_term_track_count": len(long_t),
        "medium_term_track_count": len(med_t),
        "short_term_track_count": len(short_t),
        "saved_track_count": len(saved),
        "recent_plays_in_window": len(recent_df),
    }

    insights: list[str] = [
        (
            f"Spotify member since **{member_since_year}** (~**{years_on_spotify} years**). "
            "The API does not expose lifetime play counts; this view uses **top tracks**, "
            "**saved library**, and **recent plays** as your listening fingerprint."
        ),
        (
            f"**{unique_songs}** unique songs across merged API windows "
            f"({metrics['long_term_track_count']} all-time top · "
            f"{metrics['medium_term_track_count']} six-month · "
            f"{metrics['short_term_track_count']} four-week · "
            f"{metrics['saved_track_count']} saved · "
            f"{metrics['recent_plays_in_window']} recent plays in fetch window)."
        ),
        (
            f"**{unique_artists_catalog}** artists in your editorial catalog "
            f"({unique_artists_in_tracks} represented in merged top/recent/saved tracks)."
        ),
    ]

    if not genre_div.empty:
        top_g = genre_div.iloc[0]
        insights.append(
            f"Artist **genre** lean: **{top_g['division']}** ({int(top_g['count'])} artists)."
        )
    if not region_div.empty:
        top_r = region_div.iloc[0]
        insights.append(
            f"Artist **market / region** lean: **{top_r['division']}** ({int(top_r['count'])} artists)."
        )

    narrative = _tenure_narrative(metrics, insights)

    return {
        "metrics": metrics,
        "union_tracks": union.sort_values("track_name") if not union.empty else union,
        "long_term_tracks": long_enriched,
        "medium_term_tracks": med_enriched,
        "genre_divisions": genre_div,
        "region_divisions": region_div,
        "scene_divisions": scene_div,
        "insights": insights,
        "narrative": narrative,
    }


def _tenure_narrative(metrics: dict, insights: list[str]) -> str:
    y = metrics.get("years_on_spotify", 0)
    since = metrics.get("member_since_year", SPOTIFY_MEMBER_SINCE_YEAR)
    songs = metrics.get("unique_songs_merged", 0)
    return (
        f"### Listening tenure — API evidence (~{y} years on Spotify)\n\n"
        f"Since **{since}**, your programming taste is inferred from Spotify’s **top tracks** "
        f"(including “all time” = `{TIME_RANGE_LABELS['long_term']}`), not lifetime play counts.\n\n"
        f"Merged catalog: **{songs}** unique songs and **{metrics.get('unique_artists_catalog', 0)}** "
        "artists with editorial divisions below.\n\n"
        + "\n".join(f"- {i}" for i in insights[:6])
    )


def summarize_tenure_for_role_fit(analysis: dict) -> str:
    m = analysis.get("metrics") or {}
    if not m.get("unique_songs_merged"):
        return ""
    return (
        f"Spotify since {m['member_since_year']} (~{m['years_on_spotify']} yrs); "
        f"{m['unique_songs_merged']} unique songs and {m['unique_artists_catalog']} artists "
        f"across API top-track windows (no lifetime play counts via API)."
    )
