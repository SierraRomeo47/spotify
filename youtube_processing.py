"""YouTube Takeout and culture-signal processing."""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from io import BytesIO, StringIO

import pandas as pd

MUSIC_KEYWORDS = [
    "official video",
    "official audio",
    "lyrics",
    "feat.",
    "ft.",
    "music video",
    "vevo",
    "topic",
    "remix",
    "live",
    "audio",
    "mv",
    "single",
]


def parse_youtube_takeout(file) -> pd.DataFrame:
    """Parse uploaded Takeout JSON/HTML or CSV bytes."""
    raw = file.read() if hasattr(file, "read") else file
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = str(raw)

    # JSON Takeout
    if text.strip().startswith("{") or text.strip().startswith("["):
        try:
            data = json.loads(text)
            rows = []
            items = data if isinstance(data, list) else data.get("items", data.get("watchHistory", []))
            if not items and isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        items = v
                        break
            for item in items or []:
                title = item.get("title", item.get("name", ""))
                url = item.get("titleUrl", item.get("url", ""))
                if isinstance(url, list):
                    url = url[0] if url else ""
                subs = item.get("subtitles", [])
                channel = subs[0].get("name", "") if subs else item.get("channel", "")
                watched = item.get("time", item.get("watchedAt", ""))
                rows.append({"title": title, "channel": channel, "url": url, "watched_at": watched})
            return pd.DataFrame(rows)
        except json.JSONDecodeError:
            pass

    # CSV upload
    if "," in text[:500] and "title" in text.lower()[:200]:
        return pd.read_csv(StringIO(text))

    # HTML fallback
    rows = []
    for m in re.finditer(r"<a[^>]*href=\"([^\"]+)\"[^>]*>([^<]+)</a>", text):
        url, title = m.group(1), m.group(2)
        if "youtube" in url:
            rows.append({"title": title, "channel": "", "url": url, "watched_at": ""})
    return pd.DataFrame(rows)


def normalize_youtube_history(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "title",
                "channel",
                "url",
                "watched_at",
                "source",
                "manual_artist",
                "manual_track",
                "manual_genre",
            ]
        )
    out = df.copy()
    for col in ["title", "channel", "url", "watched_at", "manual_artist", "manual_track", "manual_genre"]:
        if col not in out.columns:
            out[col] = ""
    out["source"] = out.get("source", "upload")
    out["watched_at"] = pd.to_datetime(out["watched_at"], errors="coerce")
    return out


def extract_music_entries(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    combined = (df["title"].astype(str) + " " + df["channel"].astype(str)).str.lower()
    mask = combined.apply(lambda s: any(kw in s for kw in MUSIC_KEYWORDS))
    manual = df["manual_artist"].astype(str).str.len() > 0
    return df[mask | manual].copy()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def match_youtube_to_spotify(
    youtube_df: pd.DataFrame,
    spotify_artists_df: pd.DataFrame,
    spotify_tracks_df: pd.DataFrame | None = None,
    threshold: float = 0.85,
) -> pd.DataFrame:
    if youtube_df.empty:
        return pd.DataFrame()
    artists = []
    if not spotify_artists_df.empty:
        artists = spotify_artists_df["artist_name"].dropna().unique().tolist()

    rows = []
    for _, yt in youtube_df.iterrows():
        candidate = str(yt.get("manual_artist", "")).strip() or str(yt.get("channel", "")).strip()
        title = str(yt.get("title", ""))
        if not candidate:
            for a in artists:
                if a.lower() in title.lower():
                    candidate = a
                    break
        best_match = ""
        best_score = 0.0
        for a in artists:
            score = _similar(candidate, a) if candidate else _similar(title, a)
            if score > best_score:
                best_score = score
                best_match = a
        rows.append(
            {
                **yt.to_dict(),
                "matched_spotify_artist": best_match if best_score >= threshold else "",
                "match_score": round(best_score, 3),
                "overlap": best_score >= threshold,
            }
        )
    return pd.DataFrame(rows)
