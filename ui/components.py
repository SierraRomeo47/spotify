"""Reusable UI components."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import streamlit as st

from config import ACCENT, ASSETS_DIR, CARD, PROFILE_PILLS, PROFILE_TAGLINE
from utils.io import export_csv


def get_session_df(key: str) -> pd.DataFrame:
    """Safe session DataFrame — avoids pandas truth-value error with `or`."""
    val = st.session_state.get(key)
    if val is None:
        return pd.DataFrame()
    if isinstance(val, pd.DataFrame):
        return val
    return pd.DataFrame()


def get_session_dict(key: str) -> dict:
    val = st.session_state.get(key)
    return val if isinstance(val, dict) else {}


def missing_data_warning(what: str):
    st.info(
        f"No **{what}** loaded yet. The app auto-loads Exportify and Spotify on startup. "
        "If this persists, check sidebar **Data source** for warnings or use **Re-run full bootstrap**."
    )


def has_listening_data() -> bool:
    for key in ("tracks", "artists", "recent", "recent_history", "saved_tracks", "exportify_master"):
        df = get_session_df(key)
        if not df.empty:
            return True
    if get_session_dict("playlist_tracks"):
        return True
    return False


def data_source_caption():
    source = st.session_state.get("data_source", "none")
    stats = st.session_state.get("exportify_stats") or {}
    if source in ("exportify", "api+exportify") and stats:
        st.caption(
            f"Data: **{source}** · Exportify: {stats.get('playlists', 0)} playlists, "
            f"{stats.get('master_tracks', 0)} enriched tracks, "
            f"{stats.get('liked_tracks', 0)} liked songs."
        )
    elif source != "none":
        st.caption(f"Data source: **{source}**")


def require_listening_data(message: str = "listening data") -> bool:
    if has_listening_data():
        return True
    missing_data_warning(message)
    return False


def export_buttons(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    if df is None or df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv")
    if st.button(f"Save to outputs/{filename}", key=f"save_{filename}"):
        path = export_csv(df, filename)
        st.success(f"Saved to {path}")


def pill_row(labels: list[str] | None = None):
    pills = labels or PROFILE_PILLS
    html = '<div class="pill-row">'
    for p in pills:
        html += f'<span class="pill">{p}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def profile_tagline_footer():
    st.markdown(
        f'<div class="tagline-footer"><span class="dash">—</span> {PROFILE_TAGLINE} <span class="dash">—</span></div>',
        unsafe_allow_html=True,
    )


def _image_to_base64(path: Path) -> str:
    data = path.read_bytes()
    ext = path.suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"


def home_hero_banner(image_path: Path | None = None):
    """Full-width portfolio banner for Home (design includes title and taglines)."""
    from config import HOME_HERO_BACKGROUND

    path = image_path or HOME_HERO_BACKGROUND
    if not path.exists():
        path = ASSETS_DIR / "profile_cover.png"
    if path.exists():
        b64 = _image_to_base64(path)
        st.markdown(
            f"""
            <div class="home-hero-banner">
                <img src="{b64}" alt="Sierra Romeo — Sumit Redu editorial portfolio" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Home banner not found at `{path}`. Add home_hero_background.png to assets/.")


def hero_cover(
    image_path: Path | None = None,
    title: str = "Sierra Romeo",
    subtitle: str = "Sumit Redu",
    tagline: str = "From DJ Instinct to Editorial Intelligence",
    pills: list[str] | None = None,
):
    path = image_path or (ASSETS_DIR / "profile_cover.png")
    if path.exists():
        b64 = _image_to_base64(path)
        st.markdown(
            f"""
            <div class="hero-cover" style="background-image: linear-gradient(
                to bottom, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.85) 70%
            ), url('{b64}');">
                <div class="hero-content">
                    <p class="hero-eyebrow">Editorial Intelligence</p>
                    <h1 class="hero-title">{title}</h1>
                    <p class="hero-name">{subtitle}</p>
                    <p class="hero-tagline">{tagline}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        pill_row(pills)
    else:
        st.warning(f"Cover image not found at `{path}`. Add profile_cover.png to assets/.")


def stat_cards(metrics: list[tuple[str, str | float, str | None]]):
    """metrics: [(label, value, delta_optional), ...]"""
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            st.metric(label, value, delta)


def data_status_banner():
    source = st.session_state.get("data_source", "—")
    profile = st.session_state.get("user_profile") or {}
    name = profile.get("display_name", "")
    chip = f"Data: **{str(source).upper()}**"
    if name:
        chip += f" · {name}"
    st.markdown(f'<div class="status-chip">{chip}</div>', unsafe_allow_html=True)


@contextmanager
def chart_section(title: str, caption: str = ""):
    with st.container(border=True):
        st.markdown(f"### {title}")
        if caption:
            st.caption(caption)
        yield


def quote_card(text: str):
    st.markdown(f'<div class="quote-card">{text}</div>', unsafe_allow_html=True)


def quote_card_md(markdown_text: str):
    with st.container(border=True):
        st.markdown(markdown_text)


def role_chip(role: str) -> str:
    return f'<span class="role-chip">{role}</span>'
