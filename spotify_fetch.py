"""Spotify API fetch layer — restricted endpoints only (no Streamlit)."""

from __future__ import annotations


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        msg = str(e)
        if "403" in msg or "development mode" in msg.lower():
            msg += " Development mode may limit some endpoints."
        return None, msg


def fetch_user_profile(_sp_token_id: str, _sp) -> tuple[dict | None, str | None]:
    data, err = _safe_call(_sp.current_user)
    if data:
        return {
            "display_name": data.get("display_name"),
            "id": data.get("id"),
            "followers": (data.get("followers") or {}).get("total"),
            "country": data.get("country"),
            "product": data.get("product"),
        }, None
    return None, err


def fetch_top_tracks(_sp_token_id: str, _sp, time_range: str = "medium_term", limit: int = 50):
    result, err = _safe_call(_sp.current_user_top_tracks, limit=limit, time_range=time_range)
    if result:
        return result.get("items", []), None
    return [], err


def fetch_top_artists(_sp_token_id: str, _sp, time_range: str = "medium_term", limit: int = 50):
    result, err = _safe_call(_sp.current_user_top_artists, limit=limit, time_range=time_range)
    if result:
        return result.get("items", []), None
    return [], err


def fetch_recently_played(_sp_token_id: str, _sp, limit: int = 50):
    result, err = _safe_call(_sp.current_user_recently_played, limit=limit)
    if result:
        return result.get("items", []), None
    return [], err


def fetch_saved_tracks(_sp_token_id: str, _sp, limit: int = 500):
    items = []
    offset = 0
    page_limit = min(50, limit)
    err = None
    while len(items) < limit:
        result, e = _safe_call(_sp.current_user_saved_tracks, limit=page_limit, offset=offset)
        if e:
            err = e
            break
        if not result:
            break
        batch = result.get("items", [])
        if not batch:
            break
        items.extend(batch)
        if not result.get("next"):
            break
        offset += page_limit
    return items[:limit], err


def fetch_user_playlists(_sp_token_id: str, _sp, limit: int = 50):
    items = []
    offset = 0
    err = None
    while len(items) < limit:
        result, e = _safe_call(_sp.current_user_playlists, limit=50, offset=offset)
        if e:
            err = e
            break
        if not result:
            break
        batch = result.get("items", [])
        items.extend(batch)
        if not result.get("next") or len(items) >= limit:
            break
        offset += 50
    return items[:limit], err


def fetch_playlist_tracks(_sp_token_id: str, _sp, playlist_id: str, limit: int = 100):
    items = []
    offset = 0
    err = None
    while len(items) < limit:
        result, e = _safe_call(_sp.playlist_items, playlist_id, limit=50, offset=offset)
        if e:
            err = e
            break
        if not result:
            break
        batch = result.get("items", [])
        items.extend(batch)
        if not result.get("next") or len(items) >= limit:
            break
        offset += 50
    return items[:limit], err


def get_token_id(sp) -> str:
    """Cache key from current user id."""
    try:
        u = sp.current_user()
        return u.get("id", "unknown")
    except Exception:
        return "anonymous"
