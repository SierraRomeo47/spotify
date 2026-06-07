"""Early discovery and breakout detection for editorial role alignment."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from config import EARLY_DISCOVERY_WEIGHTS, POPULARITY_PRE_MAINSTREAM_MAX, RECENT_RELEASE_MONTHS
from config import (
    CV_CERTIFICATIONS,
    CV_EXPERIENCE_HIGHLIGHTS,
    CV_JD_BRIDGE,
    CV_PROFILE,
    SPOTIFY_MEMBER_SINCE_YEAR,
)
from data_processing import build_artist_catalog, explode_artist_column, format_tag_label, split_artist_names


def enrich_recent_with_dates(recent_df: pd.DataFrame) -> pd.DataFrame:
    if recent_df.empty or "played_at" not in recent_df.columns:
        return recent_df
    out = recent_df.copy()
    out["played_at"] = pd.to_datetime(out["played_at"], errors="coerce", utc=True)
    out["play_date"] = out["played_at"].dt.date
    now = pd.Timestamp.now(tz=timezone.utc)
    out["days_ago"] = (now - out["played_at"]).dt.days
    return out


def build_daily_listen_timeline(recent_df: pd.DataFrame) -> pd.DataFrame:
    """Per-day plays, unique artists, and new artists first seen that day."""
    recent = enrich_recent_with_dates(recent_df)
    if recent.empty:
        return pd.DataFrame(
            columns=["play_date", "total_plays", "unique_artists", "new_artists", "new_artist_names"]
        )

    exploded = explode_artist_column(recent, "artist_name")
    artist_first = (
        exploded.groupby("artist_name")["played_at"].min().reset_index().rename(columns={"played_at": "first_played"})
    )
    exploded = exploded.merge(artist_first, on="artist_name", how="left")
    exploded["first_play_date"] = exploded["first_played"].dt.date

    rows = []
    for play_date, grp in exploded.groupby("play_date"):
        new_mask = grp["play_date"] == grp["first_play_date"]
        new_artists = grp.loc[new_mask, "artist_name"].dropna().unique().tolist()
        top_artist = grp["artist_name"].value_counts().index[0] if len(grp) else ""
        rows.append(
            {
                "play_date": play_date,
                "total_plays": len(grp),
                "unique_artists": grp["artist_name"].nunique(),
                "new_artists": len(new_artists),
                "new_artist_names": ", ".join(new_artists[:5]),
                "top_artist_that_day": top_artist,
            }
        )
    return pd.DataFrame(rows).sort_values("play_date", ascending=False)


def compute_listen_velocity(recent_df: pd.DataFrame, by: str = "artist") -> pd.DataFrame:
    """Listen counts per artist or track in the recent window."""
    recent = enrich_recent_with_dates(recent_df)
    if recent.empty:
        return pd.DataFrame()

    if by == "artist":
        recent = explode_artist_column(recent, "artist_name")

    key = "artist_name" if by == "artist" else "track_name"
    if key not in recent.columns:
        return pd.DataFrame()

    agg = (
        recent.groupby(key)
        .agg(
            listen_count=("played_at", "count"),
            first_played_at=("played_at", "min"),
            last_played_at=("played_at", "max"),
            play_dates=("play_date", lambda x: x.nunique()),
        )
        .reset_index()
    )
    agg.rename(columns={key: "name"}, inplace=True)
    agg["entity_type"] = by
    agg["first_detected_date"] = pd.to_datetime(agg["first_played_at"]).dt.date
    agg["days_active"] = agg["play_dates"]
    if by == "track" and "artist_name" in recent.columns:
        primary_artist = recent.groupby("track_name")["artist_name"].first()
        agg["artist_name"] = agg["name"].map(primary_artist)
    return agg.sort_values("listen_count", ascending=False)


def _long_term_artists(tracks_df: pd.DataFrame, artists_df: pd.DataFrame) -> set:
    names = set()
    if not tracks_df.empty and "time_range" in tracks_df.columns:
        names |= set(tracks_df[tracks_df["time_range"] == "long_term"]["artist_name"].dropna())
    if not artists_df.empty and "time_range" in artists_df.columns:
        names |= set(artists_df[artists_df["time_range"] == "long_term"]["artist_name"].dropna())
    elif not artists_df.empty:
        names |= set(artists_df["artist_name"].dropna())
    return names


def has_popularity_data(df: pd.DataFrame, col: str = "popularity") -> bool:
    """True when at least one non-null popularity value exists."""
    if df.empty or col not in df.columns:
        return False
    return bool(pd.to_numeric(df[col], errors="coerce").notna().any())


def _programming_lane(row: pd.Series) -> str:
    region = str(row.get("region_tag", "") or row.get("region", ""))
    genre = str(row.get("genre_bucket", "") or row.get("genre", ""))
    scene = str(row.get("scene_tag", "") or row.get("scene", "")).lower()
    if "India-Global" in region or "india-global" in region.lower():
        return "India · Global Bridge"
    if "India" in region:
        if "Hip-Hop" in genre or "hip-hop" in scene or "desi" in scene:
            return "India Export · Hip-Hop"
        if "drill" in scene:
            return "India Export · Drill"
        if "underground" in scene:
            return "India Export · Underground"
        return "India-Linked Programming"
    if "Global" in region or "International" in region:
        if "Electronic" in genre or "electronic" in scene or "house" in scene or "club" in scene:
            return "Global · Club Entry"
        if "Hip-Hop" in genre or "hip-hop" in scene or "drill" in scene:
            return "Global · Hip-Hop Entry"
        return "Global Entry Point"
    if "Hip-Hop" in genre:
        return "Hip-Hop Core"
    return "Crossover · Monitor"


def format_watchlist_for_display(watchlist: pd.DataFrame) -> pd.DataFrame:
    """Employer-facing watchlist: formatted tags, no internal velocity columns."""
    if watchlist.empty:
        return watchlist

    out = watchlist.copy()
    out["region"] = out["region_tag"].map(format_tag_label) if "region_tag" in out.columns else ""
    out["scene"] = out["scene_tag"].map(format_tag_label) if "scene_tag" in out.columns else ""
    out["genre"] = out["genre_bucket"].map(format_tag_label) if "genre_bucket" in out.columns else ""
    if "language" in out.columns:
        out["languages"] = out["language"].fillna("")
    elif "languages" in out.columns:
        out["languages"] = out["languages"].fillna("")
    else:
        out["languages"] = ""
    out["programming_lane"] = out.apply(_programming_lane, axis=1)
    out["editorial_action"] = out.get("suggested_editorial_action", "")

    out["_key"] = out["artist_name"].astype(str).str.strip().str.lower()
    out = out.sort_values("early_discovery_score", ascending=False).drop_duplicates("_key", keep="first")
    out = out.drop(columns=["_key"], errors="ignore")
    return out


def watchlist_display_columns(watchlist: pd.DataFrame) -> list[str]:
    """Columns for breakout watchlist table (after format_watchlist_for_display)."""
    preferred = [
        "artist_name",
        "region",
        "scene",
        "languages",
        "programming_lane",
        "early_discovery_score",
        "editorial_action",
    ]
    if has_popularity_data(watchlist, "popularity"):
        preferred.insert(-1, "popularity_band")
    return [c for c in preferred if c in watchlist.columns]


def track_watchlist_display_columns(track_watch: pd.DataFrame) -> list[str]:
    cols = [
        "track_name",
        "artist_name",
        "listen_count",
        "first_detected_date",
        "early_discovery_score",
        "is_pre_long_term_artist",
    ]
    if has_popularity_data(track_watch, "popularity"):
        cols.insert(4, "popularity_band")
    return [c for c in cols if c in track_watch.columns]


def _popularity_band(pop) -> str:
    if pd.isna(pop):
        return "Unknown"
    if pop < POPULARITY_PRE_MAINSTREAM_MAX:
        return "Pre-mainstream"
    if pop < 70:
        return "Rising"
    return "Mainstream"


def _suggested_action(row: dict) -> str:
    region = str(row.get("region_tag", ""))
    band = str(row.get("popularity_band", ""))
    if "India" in region and band == "Pre-mainstream":
        return "Flag for Indian hip-hop export / local breakout playlist"
    if "International" in region or "Global" in region:
        return "Test global→India entry-point placement"
    if band == "Pre-mainstream":
        return "Add to Breakout Watch editorial pool"
    return "Monitor listen velocity; consider sequence slot"


def compute_early_discovery_scores(
    artists_df: pd.DataFrame,
    tracks_df: pd.DataFrame,
    recent_df: pd.DataFrame,
    saved_tracks_df: pd.DataFrame | None = None,
    playlist_tracks: dict | None = None,
) -> pd.DataFrame:
    if artists_df.empty and recent_df.empty and tracks_df.empty:
        return pd.DataFrame()

    velocity = compute_listen_velocity(recent_df, "artist")
    vel_map = velocity.set_index("name") if not velocity.empty else pd.DataFrame()

    long_names = _long_term_artists(tracks_df, artists_df)
    max_listens = velocity["listen_count"].max() if not velocity.empty else 1

    base = build_artist_catalog(
        artists_df,
        tracks_df,
        recent_df,
        saved_tracks_df,
        playlist_tracks,
    )
    if base.empty and not velocity.empty:
        base = pd.DataFrame({"artist_name": velocity["name"].tolist()})

    current_year = datetime.now().year
    rows = []
    for _, a in base.iterrows():
        name = a.get("artist_name", "")
        if not name:
            continue
        listens = int(vel_map.loc[name, "listen_count"]) if not vel_map.empty and name in vel_map.index else 0
        first_date = vel_map.loc[name, "first_detected_date"] if not vel_map.empty and name in vel_map.index else None
        taste_rank = int(a.get("best_rank", 999)) if pd.notna(a.get("best_rank")) else 999

        listen_score = min(100, (listens / max(max_listens, 1)) * 100) * EARLY_DISCOVERY_WEIGHTS["listen_velocity"] / 0.30
        not_long = name not in long_names
        long_score = (100 if not_long else 20) * EARLY_DISCOVERY_WEIGHTS["not_in_long_term"] / 0.25

        pop = pd.to_numeric(a.get("popularity"), errors="coerce")
        pop_low = pd.isna(pop) or pop < POPULARITY_PRE_MAINSTREAM_MAX
        pop_score = (100 if pop_low else 30) * EARLY_DISCOVERY_WEIGHTS["low_popularity"] / 0.20

        yr = pd.to_numeric(a.get("release_year"), errors="coerce") if "release_year" in a.index else np.nan
        if pd.isna(yr) and not tracks_df.empty:
            at = tracks_df[tracks_df["artist_name"] == name]
            if not at.empty and "release_year" in at.columns:
                yr = pd.to_numeric(at["release_year"], errors="coerce").max()
        recent_release = pd.notna(yr) and yr >= current_year - (RECENT_RELEASE_MONTHS // 12 + 1)
        rec_score = (100 if recent_release or pop_low else 40) * EARLY_DISCOVERY_WEIGHTS["recent_release"] / 0.15

        has_metadata = bool(a.get("genre_bucket")) and bool(a.get("region_tag"))
        meta_score = (100 if has_metadata else 30) * EARLY_DISCOVERY_WEIGHTS["manual_editorial"] / 0.10

        taste_bonus = max(0.0, (51 - taste_rank) / 50.0 * 12) if taste_rank < 999 else 0.0
        total = listen_score + long_score + pop_score + rec_score + meta_score + taste_bonus

        row = {
            "artist_name": name,
            "listen_count_7d": listens,
            "first_detected_date": first_date,
            "is_pre_long_term": not_long,
            "popularity_band": _popularity_band(pop),
            "early_discovery_score": round(min(100, total), 1),
            "region_tag": a.get("region_tag", ""),
            "scene_tag": a.get("scene_tag", ""),
            "language": a.get("languages", "") or "",
            "genre_bucket": a.get("genre_bucket", ""),
            "popularity": pop,
            "taste_rank": taste_rank,
            "in_top_tracks": taste_rank < 999,
        }
        row["suggested_editorial_action"] = _suggested_action(row)
        rows.append(row)

    if not velocity.empty:
        for name in velocity["name"]:
            if name not in [r["artist_name"] for r in rows]:
                listens = int(velocity.loc[velocity["name"] == name, "listen_count"].iloc[0])
                if listens > 0:
                    row = {
                        "artist_name": name,
                        "listen_count_7d": listens,
                        "first_detected_date": velocity.loc[velocity["name"] == name, "first_detected_date"].iloc[0],
                        "is_pre_long_term": name not in long_names,
                        "popularity_band": "Unknown (API)",
                        "early_discovery_score": round(min(100, listens / max(max_listens, 1) * 70), 1),
                        "region_tag": "",
                        "scene_tag": "",
                        "genre_bucket": "",
                        "popularity": None,
                    }
                    row["suggested_editorial_action"] = _suggested_action(row)
                    rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(
        ["early_discovery_score", "listen_count_7d", "taste_rank"],
        ascending=[False, False, True],
    )


def build_breakout_watchlist(
    artists_df: pd.DataFrame,
    tracks_df: pd.DataFrame,
    recent_df: pd.DataFrame,
    filter_lane: str | None = None,
    saved_tracks_df: pd.DataFrame | None = None,
    playlist_tracks: dict | None = None,
) -> pd.DataFrame:
    scored = compute_early_discovery_scores(
        artists_df,
        tracks_df,
        recent_df,
        saved_tracks_df,
        playlist_tracks,
    )
    if scored.empty:
        return scored

    if filter_lane == "hiphop":
        scored = scored[scored["genre_bucket"] == "Hip-Hop/Rap"]
    elif filter_lane == "hiphop_indie":
        india = scored["region_tag"].astype(str).str.contains("India", case=False, na=False)
        hiphop = scored["genre_bucket"] == "Hip-Hop/Rap"
        scored = scored[hiphop | india]
    elif filter_lane == "india_export":
        scored = scored[scored["region_tag"].astype(str).str.contains("India", case=False, na=False)]
    elif filter_lane == "global_entry":
        scored = scored[scored["region_tag"].astype(str).str.contains("International|Global", case=False, na=False)]
    elif filter_lane == "pre_mainstream":
        scored = scored[scored["popularity_band"] == "Pre-mainstream"]
    elif filter_lane == "pre_long_term":
        scored = scored[scored["is_pre_long_term"] == True]

    return scored.sort_values(
        ["early_discovery_score", "listen_count_7d", "taste_rank"],
        ascending=[False, False, True],
    )


def build_track_breakout_watchlist(
    tracks_df: pd.DataFrame,
    recent_df: pd.DataFrame,
    artists_df: pd.DataFrame,
) -> pd.DataFrame:
    recent = enrich_recent_with_dates(recent_df)
    if recent.empty:
        return pd.DataFrame()

    long_names = _long_term_artists(tracks_df, artists_df)
    vel = recent.groupby(["track_name", "artist_name"]).agg(
        listen_count=("played_at", "count"),
        first_played_at=("played_at", "min"),
    ).reset_index()
    vel["first_detected_date"] = pd.to_datetime(vel["first_played_at"]).dt.date
    vel["is_pre_long_term_artist"] = ~vel["artist_name"].isin(long_names)

    if not tracks_df.empty:
        meta = tracks_df.drop_duplicates("track_name")[
            ["track_name", "popularity", "release_year", "release_date"]
        ]
        vel = vel.merge(meta, on="track_name", how="left", suffixes=("", "_meta"))

    max_l = vel["listen_count"].max() or 1
    vel["popularity_band"] = vel["popularity"].apply(_popularity_band) if "popularity" in vel.columns else "Unknown (API)"
    vel["early_discovery_score"] = (
        (vel["listen_count"] / max_l * 50)
        + vel["is_pre_long_term_artist"].astype(int) * 30
        + (vel["popularity_band"] == "Pre-mainstream").astype(int) * 20
    ).round(1)

    return vel.sort_values("early_discovery_score", ascending=False)


def generate_early_discovery_insights(
    watchlist: pd.DataFrame,
    daily: pd.DataFrame,
    recent_df: pd.DataFrame,
) -> list[str]:
    insights = []
    if not watchlist.empty:
        top = ", ".join(watchlist["artist_name"].head(3).tolist())
        pre = watchlist[watchlist["is_pre_long_term"] == True]
        insights.append(
            f"Breakout watchlist leaders ({top}) show listen momentum before long-term catalog lock-in."
        )
        if not pre.empty:
            insights.append(
                f"{len(pre)} artists are in your recent rotation but not yet long-term top artists — early editorial lane."
            )
    if not daily.empty:
        best_day = daily.sort_values("new_artists", ascending=False).iloc[0]
        insights.append(
            f"Peak discovery day {best_day['play_date']}: {best_day['new_artists']} new artists in your listening window."
        )
    if not recent_df.empty:
        insights.append(
            f"Recent window captures {recent_df['artist_name'].nunique()} unique artists across "
            f"{recent_df['play_date'].nunique() if 'play_date' in recent_df.columns else 'N'} listening days."
        )
    insights.append(
        "Re-fetch Spotify data after active listening sessions for fresher day-by-day signals (API returns up to 50 recent plays)."
    )
    insights.append(
        "These are personal-listening heuristics modeling editorial 'spot before mainstream' — not Spotify chart data."
    )
    while len(insights) < 5:
        insights.append("Fetch Spotify data for stronger India ↔ global programming lane signals.")
    return insights[:7]


def build_enhanced_editorial_radar(
    recent_df: pd.DataFrame,
    artists_df: pd.DataFrame,
    tracks_df: pd.DataFrame,
) -> pd.DataFrame:
    """Editorial radar with listen counts and early signals."""
    recent = enrich_recent_with_dates(recent_df)
    if recent.empty:
        return pd.DataFrame()

    long_names = _long_term_artists(tracks_df, artists_df)
    vel = compute_listen_velocity(recent, "artist")
    vel_a = vel.set_index("name") if not vel.empty else pd.DataFrame()

    rows = []
    for _, r in recent.head(50).iterrows():
        artist = r.get("artist_name", "")
        is_lt = artist in long_names
        listens = int(vel_a.loc[artist, "listen_count"]) if artist in vel_a.index else 1
        first_d = vel_a.loc[artist, "first_detected_date"] if artist in vel_a.index else r.get("play_date")
        if is_lt and listens > 2:
            signal = "Comfort"
        elif not is_lt and listens >= 2:
            signal = "Breakout"
        elif not is_lt:
            signal = "Trend"
        else:
            signal = "Core taste"
        rows.append(
            {
                "artist": artist,
                "track": r.get("track_name", ""),
                "played_at": r.get("played_at", ""),
                "listen_count": listens,
                "first_detected_date": first_d,
                "is_long_term_artist": is_lt,
                "early_signal": signal,
                "possible_editorial_signal": f"{signal} — {'repeat' if listens > 1 else 'first touch'}",
            }
        )
    return pd.DataFrame(rows)


def _long_term_artist_names(tracks_df: pd.DataFrame, artists_df: pd.DataFrame) -> set:
    names: set[str] = set()
    if not tracks_df.empty and "time_range" in tracks_df.columns:
        lt = tracks_df[tracks_df["time_range"] == "long_term"]["artist_name"].dropna()
        for a in lt:
            names.update(split_artist_names(a))
    if not artists_df.empty and "time_range" in artists_df.columns:
        lt = artists_df[artists_df["time_range"] == "long_term"]["artist_name"].dropna()
        names.update(lt.astype(str).tolist())
    return names


def _frontier_artists(
    tracks_df: pd.DataFrame,
    artists_df: pd.DataFrame,
    watchlist: pd.DataFrame,
    max_n: int = 6,
) -> str:
    long_names = _long_term_artist_names(tracks_df, artists_df)
    frontier: list[str] = []
    if not tracks_df.empty and "time_range" in tracks_df.columns:
        short = tracks_df[tracks_df["time_range"] == "short_term"]["artist_name"].dropna().unique()
        for a in short:
            for name in split_artist_names(a):
                if name and name not in long_names:
                    frontier.append(name)
    if not frontier and not watchlist.empty and "is_pre_long_term" in watchlist.columns:
        pre = watchlist[watchlist["is_pre_long_term"].fillna(False).astype(bool)]
        frontier = pre["artist_name"].head(max_n).tolist()
    unique = list(dict.fromkeys(frontier))
    return ", ".join(unique[:max_n]) if unique else "—"


def _long_term_india_global(
    tracks_df: pd.DataFrame,
    artists_df: pd.DataFrame,
) -> str:
    names: list[str] = []
    india_kw = {
        "ap dhillon", "shubh", "divine", "seedhe maut", "karan aujla", "prabh deep",
        "hanumankind", "prabh deep", "ikka", "raftaar", "king", "otaal", "otaal",
    }
    long_names = _long_term_artist_names(tracks_df, artists_df)
    for n in long_names:
        key = str(n).lower()
        if key in india_kw:
            names.append(str(n))
    if not artists_df.empty and "region_tag" in artists_df.columns:
        india = artists_df[
            artists_df["region_tag"].astype(str).str.contains("India", case=False, na=False)
        ]
        for n in india["artist_name"].head(8):
            if str(n) not in names:
                names.append(str(n))
    return ", ".join(names[:6]) if names else "—"


def _format_artist_list(names: list[str], fallback: str = "—") -> str:
    cleaned = [str(n).strip() for n in names if n and str(n).strip()]
    return ", ".join(cleaned) if cleaned else fallback


def map_role_fit_to_jd(
    watchlist: pd.DataFrame,
    track_watch: pd.DataFrame,
    daily: pd.DataFrame,
    insights: list,
    india_insights: list,
    playlist_scores: pd.DataFrame,
    mood: str,
    dj_story: str,
    artists_df: pd.DataFrame | None = None,
    tracks_df: pd.DataFrame | None = None,
    tenure_summary: str = "",
    exportify_stats: dict | None = None,
    data_source: str = "api",
) -> str:
    """Role fit mapped to Spotify Editor JD with CV evidence + live listening data."""
    artists_df = artists_df if artists_df is not None else pd.DataFrame()
    tracks_df = tracks_df if tracks_df is not None else pd.DataFrame()

    top5 = _format_artist_list(watchlist["artist_name"].head(5).tolist() if not watchlist.empty else [])
    pre_long_list: list[str] = []
    if not watchlist.empty and "is_pre_long_term" in watchlist.columns:
        pre = watchlist[watchlist["is_pre_long_term"].fillna(False).astype(bool)]
        pre_long_list = pre["artist_name"].head(6).tolist()
    pre_long = _format_artist_list(pre_long_list)
    top_tracks = _format_artist_list(track_watch["track_name"].head(3).tolist() if not track_watch.empty else [])
    frontier = _frontier_artists(tracks_df, artists_df, watchlist)
    india_core = _long_term_india_global(tracks_df, artists_df)

    hiphop_lane = []
    if not watchlist.empty and "genre_bucket" in watchlist.columns:
        hh = watchlist[watchlist["genre_bucket"] == "Hip-Hop/Rap"]
        hiphop_lane = hh["artist_name"].head(5).tolist()
    hiphop_names = _format_artist_list(hiphop_lane, "see Culture & lanes")

    discovery_day = ""
    if not daily.empty:
        d = daily.sort_values("new_artists", ascending=False).iloc[0]
        discovery_day = f"Peak discovery day **{d['play_date']}** ({int(d['new_artists'])} new artists in window)."

    pl_lines: list[str] = []
    if not playlist_scores.empty:
        for _, row in playlist_scores.head(3).iterrows():
            pl_lines.append(
                f"**{row['playlist_name']}** — cohesion {row.get('cohesion_score', 0):.0f}, "
                f"early-slot {row.get('discovery_score', 0):.0f}, "
                f"India-global bridge {row.get('india_global_bridge_score', 0):.0f}"
            )
    pl_block = "; ".join(pl_lines) if pl_lines else "Curate tab: sequenced sets with opener → peak → cooldown and editorial narrative."

    cv = CV_PROFILE
    linkedin = cv["linkedin_url"]
    india_artists = india_core if india_core != "—" else "AP Dhillon, Shubh, Divine, Seedhe Maut, OtaaL (see Culture & lanes)"

    sections = [
        f"# Role Fit — {cv['target_role']}\n",
        f"**{cv['name']}** · portfolio alias **{cv['alias']}**\n",
        f"{cv['headline']}\n",
        f"{cv['location']} · {cv['contact']}\n",
        f"LinkedIn: [{linkedin}]({linkedin})\n",
        "\n",
        "*Portfolio using authorized personal Spotify data to demonstrate editorial judgment. "
        "Not affiliated with Spotify; no access to internal chart or audience data.*\n",
        "\n",
        "### Executive summary\n",
        f"- {CV_JD_BRIDGE['experience']}",
        f"- **Dual lens (honest):** Recent listening leans **club/electronic** (e.g. Fred again.., &ME); long-term taste includes **India ↔ global hip-hop** ({india_artists}).",
        f"- {CV_JD_BRIDGE['data']}",
        f"- {CV_JD_BRIDGE['story']}",
    ]
    if tenure_summary:
        sections.append(f"- **Listening tenure (API):** {tenure_summary}")
    exp = exportify_stats or {}
    if exp.get("master_tracks") and data_source in ("exportify", "api+exportify"):
        sections.append(
            f"- **Library depth (Exportify):** {exp.get('master_tracks', 0)} unique tracks across "
            f"{exp.get('playlists', 0)} exported playlists and {exp.get('liked_tracks', 0)} liked songs — "
            "genres, popularity, and audio features from personal exports (not live chart data)."
        )
    sections.extend(
        [
        "\n",
        "---\n",
        "\n",
        "## What I'll do (job description)\n",
        "\n",
        "### 1. Spot trends, emerging artists, and cultural moments\n",
        f"- **Listening:** Recent velocity — {top5}.",
        f"- **Listening:** Artists in rotation before long-term lock-in — {pre_long}.",
        f"- **Listening:** Short-term-only frontier — {frontier}.",
        f"- **Listening:** Hip-hop / indie lane — {hiphop_names}.",
        f"- **Listening:** Early track momentum — {top_tracks}.",
        (
            f"- **Listening:** {discovery_day}"
            if discovery_day
            else "- **Listening:** Discovery page — plays per day and when new artists enter rotation."
        ),
        f"- **Professional:** {CV_JD_BRIDGE['trends']}",
        "\n",
        "### 2. Curate playlists — sequencing, storytelling, editorial voice\n",
        f"- **Listening:** {pl_block}",
        "- **Listening:** Curate — ~9-year tenure (API top tracks + artist divisions), playlist proof, and editorial concepts "
        "(*Breakout Watch*, *Global Hip-Hop: India Entry*, *Indian Hip-Hop Export*, *Club Crossover*, *Late Night Mumbai*).",
        f"- **Professional:** {CV_JD_BRIDGE['curate']}",
        "\n",
        "### 3. Bridge global music and Indian audiences; elevate Indian hip-hop globally\n",
        f"- **Listening:** Long-term anchors — **{india_core}**.",
        "- **Listening:** Recent club/electronic rotation is a bridge opportunity into India-relevant editorial slots.",
        ]
    )
    for b in india_insights[:2]:
        sections.append(f"- **Listening:** {b}")
    sections.extend(
        [
            f"- **Professional:** {CV_JD_BRIDGE['india_global']}",
            "\n",
            "### 4. Use data and audience insights\n",
        ]
    )
    for b in insights[:3]:
        sections.append(f"- **Listening:** {b}")
    sections.extend(
        [
            f"- **Listening:** Current mode — **{mood}**.",
            "- **Listening:** Scores use listen velocity and long-term vs short-term absence (popularity often unavailable in Spotify Development API).",
            f"- **Professional:** {CV_JD_BRIDGE['data']} Built FPL analytics (https://fpl-lac.vercel.app); IIM certifications in Generative AI and data-driven decision-making.",
            "\n",
            "### 5. Collaborate with editorial, marketing, and product\n",
            f"- **Professional:** {CV_JD_BRIDGE['collaborate']}",
            "\n",
            "### 6. Artist discovery and storytelling beyond playlists\n",
            "- **Listening:** Breakout watchlist — programming lane, languages, editorial action (exportable CSV).",
            f"- **Professional:** {dj_story}",
            "- **Professional:** IIM Mumbai MBA + maritime sustainability writing (FuelEU / EU ETS insights on LinkedIn).",
            "\n",
            "## Who I am (job description)\n",
            "\n",
            "| Requirement | How I match |\n",
            "|-------------|-------------|\n",
            (
                "| **6+ years in music, media, or entertainment** | "
                + (
                    f"{tenure_summary} DJ practice & gigs (2021–2023); 12 years Maersk; analytics + FPL app + this lab. |"
                    if tenure_summary
                    else (
                        f"Spotify since {SPOTIFY_MEMBER_SINCE_YEAR}; DJ practice & gigs (2021–2023); "
                        "12 years Maersk; analytics + FPL app + this lab. |"
                    )
                )
                + "\n"
            ),
            "| **Global culture, hip-hop, India** | Club/electronic in recent plays; desi hip-hop/indie in long-term taste and tagged artists ({india_artists}). |\n",
            "| **Data-led decisions** | ShipWatch/GeoServe analytics; Python dashboards; this lab. |\n",
            "| **English (+ Indian languages a plus)** | Professional English for clients and verifiers; Hindi/regional context via India programming lanes. |\n",
            "| **Collaboration, fast-paced environment** | Cross-functional maritime tech, verifier partnerships, MBA cohort. |\n",
            "\n",
            "## Where I'll be\n",
            "\n",
            f"- **Mumbai, Maharashtra** — matches role location; open to hybrid work per JD.\n",
            "\n",
            "## Experience (from LinkedIn)\n",
            "\n",
        ]
    )
    for item in CV_EXPERIENCE_HIGHLIGHTS:
        sections.append(f"- {item}")
    sections.extend(["\n", "## Certifications\n", "\n"])
    for item in CV_CERTIFICATIONS:
        sections.append(f"- {item}")
    sections.extend(
        [
            "\n",
            "---\n",
            "*Portfolio demonstration only — not affiliated with Spotify. Listening metrics are personal-data heuristics, not official Spotify KPIs.*",
        ]
    )
    return "\n".join(s for s in sections if s is not None and s != "")


def discovery_summary_metrics(watchlist: pd.DataFrame, recent_df: pd.DataFrame) -> dict:
    recent = enrich_recent_with_dates(recent_df)
    exploded = explode_artist_column(recent, "artist_name") if not recent.empty else recent
    new_artists = 0
    if not watchlist.empty:
        new_artists = int((watchlist["is_pre_long_term"] == True).sum())
    return {
        "new_artists_pre_long_term": new_artists,
        "pre_long_term_listen_events": 0,
        "avg_listens_per_candidate": 0.0,
        "unique_artists_in_window": int(exploded["artist_name"].nunique()) if not exploded.empty else 0,
    }
