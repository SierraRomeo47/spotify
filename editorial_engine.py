"""Editorial insights, scoring, sequencing, and role-fit summaries."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from config import EDITORIAL_CONCEPTS, POPULARITY_PRE_MAINSTREAM_MAX, SCORE_WEIGHTS, SEQUENCE_ROLES
from data_processing import (
    calculate_repeat_affinity,
    classify_genres,
    enrich_tracks_with_artist_metadata,
)


def generate_listening_insights(tracks_df: pd.DataFrame, artists_df: pd.DataFrame) -> list[str]:
    insights: list[str] = []
    if tracks_df.empty and artists_df.empty:
        return ["Connect Spotify in the sidebar to generate listening insights."]

    affinity_source = artists_df
    if not artists_df.empty and "time_range" not in artists_df.columns and not tracks_df.empty:
        affinity_source = tracks_df
    if not affinity_source.empty and "time_range" in affinity_source.columns:
        repeat = calculate_repeat_affinity(affinity_source)
        high = repeat[repeat["terms_present"] >= 3]
        if not high.empty:
            names = ", ".join(high["artist_name"].head(3).tolist())
            insights.append(
                f"Your long-term listening shows high repeat affinity toward {names}, "
                "suggesting a stable editorial taste base."
            )

    if "time_range" in tracks_df.columns:
        short = tracks_df[tracks_df["time_range"] == "short_term"]["artist_name"].value_counts().head(3)
        long_ = tracks_df[tracks_df["time_range"] == "long_term"]["artist_name"].value_counts().head(10)
        if not short.empty:
            new_artists = [a for a in short.index if a not in long_.index]
            if new_artists:
                insights.append(
                    f"Your recent listening has shifted toward {', '.join(new_artists[:3])}, "
                    "indicating current discovery momentum."
                )

    if "popularity" in tracks_df.columns:
        pop = pd.to_numeric(tracks_df["popularity"], errors="coerce").dropna()
        if len(pop):
            med = pop.median()
            if med >= 70:
                insights.append(
                    f"Median track popularity is {med:.0f}/100 — mainstream-leaning listening profile."
                )
            elif med < 50:
                insights.append(
                    f"Median track popularity is {med:.0f}/100 — discovery-forward, below-mainstream tilt."
                )

    if "release_year" in tracks_df.columns:
        years = pd.to_numeric(tracks_df["release_year"], errors="coerce").dropna()
        if len(years):
            recent_pct = (years >= datetime.now().year - 2).mean() * 100
            insights.append(
                f"{recent_pct:.0f}% of top tracks released in the last two years — "
                + ("recency-weighted taste." if recent_pct > 40 else "catalog-depth orientation.")
            )

    if "explicit" in tracks_df.columns:
        ratio = tracks_df["explicit"].astype(bool).mean() * 100
        insights.append(f"Explicit content represents {ratio:.0f}% of analyzed tracks.")

    if "duration_min" in tracks_df.columns:
        avg_d = pd.to_numeric(tracks_df["duration_min"], errors="coerce").mean()
        if pd.notna(avg_d):
            insights.append(f"Average track length is {avg_d:.1f} minutes — useful for DJ set pacing.")

    return insights[:7]


def generate_india_global_insights(artists_df: pd.DataFrame) -> list[str]:
    if artists_df.empty:
        return ["Connect Spotify to load artist data for India ↔ Global bridge insights."]
    insights = []
    region = artists_df.get("region_tag", pd.Series(dtype=str)).astype(str)
    india = artists_df[region.str.contains("India", case=False, na=False)]
    global_ = artists_df[region.str.contains("International|Global", case=False, na=False)]

    if not global_.empty:
        gnames = ", ".join(global_["artist_name"].head(3).tolist())
        insights.append(
            f"Artists with high global relevance ({gnames}) are candidates for "
            "international-to-India playlist concepts."
        )
    if not india.empty:
        inames = ", ".join(india["artist_name"].head(3).tolist())
        insights.append(
            f"India-linked artists ({inames}) with repeat appearances can be flagged for export potential."
        )
    gr = artists_df.get("genre_bucket", pd.Series(dtype=str))
    hh = (gr == "Hip-Hop/Rap").sum()
    if hh:
        insights.append(f"{hh} artists classified as Hip-Hop/Rap — core lane for editorial positioning.")
    return insights[:6]


def calculate_artist_editorial_score(
    artists_df: pd.DataFrame,
    tracks_df: pd.DataFrame,
    recent_df: pd.DataFrame,
) -> pd.DataFrame:
    if artists_df.empty:
        return pd.DataFrame()

    base = artists_df.drop_duplicates("artist_name").copy()
    repeat = calculate_repeat_affinity(artists_df)
    base = base.merge(repeat, on="artist_name", how="left")
    base["terms_present"] = base["terms_present"].fillna(1)

    recent_artists = set()
    if not recent_df.empty and "artist_name" in recent_df.columns:
        recent_artists = set(recent_df["artist_name"].dropna())

    long_artists = set()
    if not tracks_df.empty and "time_range" in tracks_df.columns:
        long_artists = set(
            tracks_df[tracks_df["time_range"] == "long_term"]["artist_name"].dropna()
        )

    rows = []
    for _, a in base.iterrows():
        name = a["artist_name"]
        rank = pd.to_numeric(a.get("rank"), errors="coerce") or 50
        terms = int(a.get("terms_present", 1))

        affinity = min(40, (4 - min(rank, 50) / 12) * 10 + terms * 5)
        in_recent = name in recent_artists
        in_long = name in long_artists
        discovery = 0.0
        if in_recent and not in_long:
            discovery += 18
        elif in_recent:
            discovery += 8
        pop = pd.to_numeric(a.get("popularity"), errors="coerce")
        if pd.notna(pop) and 35 <= pop <= 65:
            discovery += 7

        india = 12 if "India" in str(a.get("region_tag", "")) else 3
        global_ = (
            12
            if "International" in str(a.get("region_tag", "")) or "Global" in str(a.get("region_tag", ""))
            else 4
        )
        club = 10 if "club" in str(a.get("scene_tag", "")).lower() else 5

        editorial = (
            SCORE_WEIGHTS["affinity"] * affinity
            + SCORE_WEIGHTS["discovery"] * discovery
            + SCORE_WEIGHTS["india"] * india
            + SCORE_WEIGHTS["global"] * global_
            + SCORE_WEIGHTS["club"] * club
        )

        rows.append(
            {
                **{k: a[k] for k in a.index if k not in ("terms_present", "repeat_affinity")},
                "personal_affinity_score": round(affinity, 1),
                "discovery_potential_score": round(discovery, 1),
                "india_relevance_score": round(india, 1),
                "global_relevance_score": round(global_, 1),
                "club_relevance_score": round(club, 1),
                "editorial_opportunity_score": round(editorial, 1),
                "repeat_affinity": a.get("repeat_affinity", "Low"),
                "in_recent": in_recent,
            }
        )
    return pd.DataFrame(rows).sort_values("editorial_opportunity_score", ascending=False)


def score_playlists(
    playlist_tracks: dict[str, pd.DataFrame], artists_df: pd.DataFrame
) -> pd.DataFrame:
    from data_processing import aggregate_playlist_stats

    rows = []
    for pid, pdf in playlist_tracks.items():
        stats = aggregate_playlist_stats(pdf, artists_df)
        if not stats:
            continue
        df = enrich_tracks_with_artist_metadata(pdf, artists_df)
        genres = df.get("genre_bucket", pd.Series(["Other"] * len(df)))
        if len(genres):
            shares = genres.value_counts(normalize=True)
            hhi = (shares**2).sum() * 100
            cohesion = min(100, hhi * 1.2)
        else:
            cohesion = 50
        discovery = stats.get("discovery_pct", 0)
        mainstream = stats.get("avg_popularity", 50)
        recency = stats.get("recency_pct", 0)
        bridge = min(stats.get("india_share", 0), stats.get("intl_share", 0)) * 2
        bridge = min(100, bridge)
        pname = df["playlist_name"].iloc[0] if "playlist_name" in df.columns and len(df) else pid
        rows.append(
            {
                "playlist_id": pid,
                "playlist_name": pname,
                "cohesion_score": round(cohesion, 1),
                "discovery_score": round(discovery, 1),
                "mainstream_score": round(mainstream, 1),
                "recency_score": round(recency, 1),
                "india_global_bridge_score": round(bridge, 1),
                **stats,
            }
        )
    return pd.DataFrame(rows)


def generate_editorial_note(row: dict | pd.Series, concept: str) -> str:
    parts = []
    if row.get("region_tag"):
        parts.append(str(row["region_tag"]))
    if row.get("genre_bucket"):
        parts.append(str(row["genre_bucket"]))
    pop = row.get("popularity")
    if pd.notna(pop):
        if pop < 40:
            parts.append("discovery slot")
        elif pop > 75:
            parts.append("mainstream anchor")
    if row.get("explicit"):
        parts.append("explicit")
    yr = row.get("release_year")
    if pd.notna(yr) and yr >= datetime.now().year - 1:
        parts.append("recent release")
    reason = ", ".join(parts) if parts else "flow placement"
    return f"{concept}: {reason}"


def _concept_filter_sort(tracks_df: pd.DataFrame, concept: str) -> pd.DataFrame:
    df = tracks_df.copy()
    if df.empty:
        return df
    if "genre_bucket" not in df.columns:
        df = df.copy()

    if concept == "Breakout Watch: Pre-Mainstream":
        pop = pd.to_numeric(df.get("popularity"), errors="coerce")
        mask = pop.isna() | (pop < POPULARITY_PRE_MAINSTREAM_MAX)
        if "release_year" in df.columns:
            yr = pd.to_numeric(df["release_year"], errors="coerce")
            mask = mask | (yr >= datetime.now().year - 2)
        df = df[mask] if mask.any() else df
        sort_col = "rank" if "rank" in df.columns else "popularity"
        df = df.sort_values(sort_col, ascending=True, na_position="last")
    elif concept == "Global Hip-Hop: India Entry Points":
        mask = df.get("region_tag", "").astype(str).str.contains("International|Global", case=False, na=False) | (
            df.get("genre_bucket") == "Hip-Hop/Rap"
        )
        df = df[mask] if mask.any() else df
        df = df.sort_values(["popularity", "release_year"], ascending=[False, False])
    elif concept == "Indian Hip-Hop Export Radar":
        mask = df.get("region_tag", "").astype(str).str.contains("India", case=False, na=False)
        df = df[mask] if mask.any() else df
        df = df.sort_values("popularity", ascending=False)
    elif concept == "Late Night Mumbai Flow":
        mask = df.get("region_tag", "").astype(str).str.contains("India", case=False, na=False)
        df = df[mask] if mask.any() else df
        df = df.sort_values(["popularity", "duration_min"], ascending=[True, False])
    elif concept == "High-Energy Club Crossover":
        mask = df.get("genre_bucket", "").isin(["Electronic/Club", "Hip-Hop/Rap", "Dancehall"])
        df = df[mask] if mask.any() else df
        df = df.sort_values("popularity", ascending=False)
    else:
        df = df.sort_values("rank" if "rank" in df.columns else "popularity", ascending=True)
    return df.head(30)


def _assign_roles(n: int) -> list[str]:
    if n == 0:
        return []
    breakpoints = [0.0, 0.10, 0.25, 0.50, 0.75, 0.85, 1.0]
    roles = []
    for i in range(n):
        pct = (i + 1) / n
        for j, role in enumerate(SEQUENCE_ROLES):
            if breakpoints[j] < pct <= breakpoints[j + 1]:
                roles.append(role)
                break
        else:
            roles.append(SEQUENCE_ROLES[-1])
    return roles


def generate_playlist_sequence(
    tracks_df: pd.DataFrame,
    concept: str,
) -> tuple[pd.DataFrame, str]:
    filtered = _concept_filter_sort(tracks_df, concept)
    if filtered.empty:
        return pd.DataFrame(), "No tracks available for this concept."

    roles = _assign_roles(len(filtered))
    rows = []
    for i, (_, row) in enumerate(filtered.iterrows()):
        rows.append(
            {
                "sequence_order": i + 1,
                "role": roles[i],
                "track": row.get("track_name", ""),
                "artist": row.get("artist_name", ""),
                "reason_for_placement": generate_editorial_note(row, concept),
                "editorial_note": row.get("editorial_note", ""),
            }
        )
    seq_df = pd.DataFrame(rows)
    copy = generate_editorial_copy(seq_df, concept)
    return seq_df, copy


def generate_editorial_copy(seq_df: pd.DataFrame, concept: str) -> str:
    if seq_df.empty:
        return "Add tracks to generate editorial sequence copy."
    opener = seq_df[seq_df["role"] == "Opener"]
    peak = seq_df[seq_df["role"] == "Peak"]
    cooldown = seq_df[seq_df["role"] == "Cooldown"]
    mid = seq_df[seq_df["role"].isin(["Early Build", "Momentum"])]

    o = opener.iloc[0] if not opener.empty else seq_df.iloc[0]
    p = peak.iloc[0] if not peak.empty else seq_df.iloc[len(seq_df) // 2]
    c = cooldown.iloc[-1] if not cooldown.empty else seq_df.iloc[-1]
    m_artists = ", ".join(mid["artist"].head(3).tolist()) if not mid.empty else "varied artists"

    return (
        f"**{concept}**\n\n"
        f"This sequence opens with **{o['track']}** by {o['artist']} ({o['role']}) — "
        f"establishing tone without peak energy too early.\n\n"
        f"The middle section builds through {m_artists}, layering momentum and scene identity.\n\n"
        f"The peak moment is **{p['track']}** by {p['artist']} — the editorial anchor of the set.\n\n"
        f"The cooldown keeps the mood with **{c['track']}** by {c['artist']}, "
        f"leaving room for reflection or a softer landing."
    )


def analyze_recent_behaviour(
    recent_df: pd.DataFrame, artists_df: pd.DataFrame
) -> tuple[str, pd.DataFrame]:
    if recent_df.empty:
        return "unknown", pd.DataFrame()

    long_names = set()
    if not artists_df.empty and "time_range" in artists_df.columns:
        long_names = set(
            artists_df[artists_df["time_range"] == "long_term"]["artist_name"].dropna()
        )
    elif not artists_df.empty:
        long_names = set(artists_df["artist_name"].dropna())

    recent_names = recent_df["artist_name"].dropna().unique()
    overlap = sum(1 for a in recent_names if a in long_names)
    ratio = overlap / max(len(recent_names), 1)
    mood = "comfort/repeat listening" if ratio >= 0.6 else "discovery/listening exploration"

    radar = []
    for _, r in recent_df.head(40).iterrows():
        artist = r.get("artist_name", "")
        is_lt = artist in long_names
        signal = "Core taste reinforcement" if is_lt else "Discovery / trend signal"
        radar.append(
            {
                "artist": artist,
                "track": r.get("track_name", ""),
                "played_at": r.get("played_at", ""),
                "is_long_term_artist": is_lt,
                "possible_editorial_signal": signal,
            }
        )
    return mood, pd.DataFrame(radar)


def generate_role_fit_summary(
    insights: list[str],
    artist_scores: pd.DataFrame,
    playlist_scores: pd.DataFrame,
    india_insights: list[str],
    mood: str,
) -> str:
    top_artists = ""
    if not artist_scores.empty:
        top_artists = ", ".join(artist_scores["artist_name"].head(5).tolist())

    pl_example = ""
    if not playlist_scores.empty:
        best = playlist_scores.sort_values("india_global_bridge_score", ascending=False).iloc[0]
        pl_example = f"Playlist **{best['playlist_name']}** scores {best['india_global_bridge_score']:.0f} on India-global bridge."

    sections = [
        "# Role Fit Summary — Editor, Music & Culture\n",
        "## 1. Editorial POV\n",
        "- Sierra Romeo bridges DJ instinct with data-led editorial thinking for Mumbai and global hip-hop lanes.\n",
        "- Taste base combines desi hip-hop depth with international crossover curiosity.\n",
        "",
        "## 2. Data-led listening insight\n",
    ]
    for b in insights[:5]:
        sections.append(f"- {b}")
    sections.extend(
        [
            "",
            "## 3. Playlist strategy example\n",
            f"- {pl_example or 'Use Playlist & Curation page metrics to cite cohesion vs discovery scores in interviews.'}",
            "- Editorial Playlist Builder demonstrates rule-based sequencing without audio_features.",
            "",
            "## 4. Hip-hop / international lens\n",
        ]
    )
    for b in india_insights[:4]:
        sections.append(f"- {b}")
    sections.extend(
        [
            "",
            "## 5. India-global culture bridge\n",
            "- Position India-linked artists with export narratives; pair global hip-hop with India entry-point framing.",
            "",
            "## 6. Interview talking points\n",
            f"- Core editorial taste anchors: {top_artists or 'connect Spotify to populate'}.",
            f"- Recent listening mode: **{mood}**.",
            "- Heuristic scores are internal editorial tools, not official Spotify metrics.",
            "- Portfolio built with authorized personal data; demonstrates culture + analytics fluency.",
            "",
            "---\n",
            "*Generated by Sierra Romeo Editorial Intelligence Lab — Sumit Redu*",
        ]
    )
    return "\n".join(sections)
