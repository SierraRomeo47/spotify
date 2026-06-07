#!/usr/bin/env python
"""Probe Spotify Web API endpoints with the configured client ID + OAuth cache."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from spotify_auth import get_spotify_client


def probe(label: str, fn, *args, **kwargs) -> dict:
    try:
        data = fn(*args, **kwargs)
        if data is None:
            return {"label": label, "status": "OK", "detail": "empty/null response"}
        if isinstance(data, list):
            return {"label": label, "status": "OK", "detail": f"{len(data)} items"}
        if isinstance(data, dict):
            if "items" in data:
                n = len(data.get("items") or [])
                extra = []
                if data.get("items"):
                    first = data["items"][0]
                    if isinstance(first, dict):
                        extra.append(f"first_keys={list(first.keys())[:8]}")
                return {"label": label, "status": "OK", "detail": f"{n} items" + ("; " + "; ".join(extra) if extra else "")}
            keys = list(data.keys())[:10]
            return {"label": label, "status": "OK", "detail": f"keys={keys}"}
        return {"label": label, "status": "OK", "detail": str(type(data).__name__)}
    except Exception as e:
        msg = str(e)
        code = "403" if "403" in msg else "401" if "401" in msg else "404" if "404" in msg else "ERR"
        return {"label": label, "status": code, "detail": msg[:180]}


def main() -> int:
    sp, err = get_spotify_client(open_browser=False)
    if err:
        print(f"FAIL: {err}")
        return 1

    me = sp.current_user()
    uid = me.get("id")
    print(f"User: {me.get('display_name')} ({uid})\n")

    # Resolve a playlist id if any
    pl_resp = sp.current_user_playlists(limit=1)
    pl_items = pl_resp.get("items") or []
    pl_id = pl_items[0]["id"] if pl_items else None
    pl_name = pl_items[0]["name"] if pl_items else None

    # Resolve sample track/artist ids from top tracks
    tt = sp.current_user_top_tracks(limit=1, time_range="short_term")
    track_id = None
    artist_id = None
    track_uri = None
    if tt.get("items"):
        t = tt["items"][0]
        track_id = t.get("id")
        track_uri = t.get("uri")
        artists = t.get("artists") or []
        artist_id = artists[0]["id"] if artists else None

    tests = [
        ("GET /me (current_user)", sp.current_user),
        ("GET /me/top/tracks", lambda: sp.current_user_top_tracks(limit=3, time_range="short_term")),
        ("GET /me/top/artists", lambda: sp.current_user_top_artists(limit=3, time_range="short_term")),
        ("GET /me/player/recently-played", lambda: sp.current_user_recently_played(limit=3)),
        ("GET /me/tracks (saved)", lambda: sp.current_user_saved_tracks(limit=3)),
        ("GET /me/playlists", lambda: sp.current_user_playlists(limit=3)),
    ]

    if pl_id:
        tests.extend([
            (f"GET /playlists/{{id}}/items ({pl_name})", lambda: sp.playlist_items(pl_id, limit=3)),
            (f"GET /playlists/{{id}} (metadata)", lambda: sp.playlist(pl_id)),
            (f"GET /playlists/{{id}}/tracks (legacy)", lambda: sp.playlist_tracks(pl_id, limit=3)),
        ])

    if track_id:
        tests.extend([
            ("GET /tracks/{id}", lambda: sp.track(track_id)),
            ("GET /tracks/{id} (popularity field)", lambda: sp.track(track_id)),
            ("GET /audio-features/{id}", lambda: sp.audio_features([track_id])),
            ("GET /audio-analysis/{id}", lambda: sp.audio_analysis(track_id)),
        ])

    if artist_id:
        tests.extend([
            ("GET /artists/{id}", lambda: sp.artist(artist_id)),
            ("GET /artists/{id}/top-tracks", lambda: sp.artist_top_tracks(artist_id, country="IN")),
            ("GET /artists/{id}/related-artists", lambda: sp.artist_related_artists(artist_id)),
            ("GET /artists/{id}/albums", lambda: sp.artist_albums(artist_id, limit=3)),
        ])

    tests.extend([
        ("GET /recommendations", lambda: sp.recommendations(seed_tracks=[track_id] if track_id else [], limit=3)),
        ("GET /browse/new-releases", lambda: sp.new_releases(country="IN", limit=3)),
        ("GET /browse/categories", lambda: sp.categories(country="IN", limit=3)),
        ("GET /search (track)", lambda: sp.search("fred again", type="track", limit=3)),
        ("GET /me/player/currently-playing", sp.current_user_playing_track),
    ])

    results = [probe(label, fn) for label, fn in tests]

    ok = [r for r in results if r["status"] == "OK"]
    blocked = [r for r in results if r["status"] == "403"]
    other = [r for r in results if r["status"] not in ("OK", "403")]

    print("=== OK ===")
    for r in ok:
        print(f"  {r['label']}: {r['detail']}")

    print("\n=== 403 / BLOCKED ===")
    for r in blocked:
        print(f"  {r['label']}: {r['detail']}")

    print("\n=== OTHER ===")
    for r in other:
        print(f"  [{r['status']}] {r['label']}: {r['detail']}")

    # Field-level check on artist + track
    if artist_id:
        a = sp.artist(artist_id)
        print("\n=== Artist object fields (live) ===")
        print(json.dumps({
            "name": a.get("name"),
            "genres": a.get("genres"),
            "popularity": a.get("popularity"),
            "followers": (a.get("followers") or {}).get("total"),
            "keys": list(a.keys()),
        }, indent=2))

    if track_id:
        t = sp.track(track_id)
        print("\n=== Track object fields (live) ===")
        print(json.dumps({
            "name": t.get("name"),
            "popularity": t.get("popularity"),
            "explicit": t.get("explicit"),
            "keys": list(t.keys()),
        }, indent=2))

    print(f"\nSummary: {len(ok)} OK, {len(blocked)} blocked (403), {len(other)} other")
    return 0


if __name__ == "__main__":
    sys.exit(main())
