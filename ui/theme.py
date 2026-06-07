"""Streamlit theme and CSS."""

import streamlit as st

from config import (
    ACCENT,
    ACCENT_RED,
    APP_SUBTITLE,
    APP_TITLE,
    BG,
    BG_ELEVATED,
    CARD,
    CARD_ELEVATED,
    DISCLAIMER,
    FOOTER_TAGLINE,
    MUTED,
    TEXT,
)


def inject_custom_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        .stApp {{
            background-color: {BG};
            color: {TEXT};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        [data-testid="stSidebar"] {{
            background-color: {BG_ELEVATED} !important;
            border-right: 1px solid #282828;
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{
            color: {TEXT} !important;
        }}
        h1, h2, h3, h4, p, label, .stMarkdown {{
            color: {TEXT};
        }}
        .stCaption {{ color: {MUTED} !important; }}

        /* Hero */
        .hero-cover {{
            width: 100%;
            min-height: 380px;
            background-size: cover;
            background-position: center top;
            border-radius: 12px;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-end;
            overflow: hidden;
            border: 1px solid #282828;
        }}
        .hero-content {{
            padding: 2rem 2.5rem;
            width: 100%;
        }}
        .hero-eyebrow {{
            color: {ACCENT};
            font-size: 0.75rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            margin: 0 0 0.5rem 0;
        }}
        .hero-title {{
            font-size: 3.5rem;
            font-weight: 700;
            line-height: 1;
            margin: 0;
            color: {TEXT} !important;
        }}
        .hero-name {{
            font-size: 1.5rem;
            color: {ACCENT} !important;
            margin: 0.25rem 0;
            font-weight: 600;
        }}
        .hero-tagline {{
            color: {MUTED};
            font-size: 1rem;
            margin: 0.5rem 0 0 0;
        }}

        /* Home — full portfolio banner; scale to width, never crop */
        .home-hero-banner {{
            width: 100%;
            margin: -1rem 0 1.5rem 0;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #282828;
            line-height: 0;
            background: {BG};
        }}
        .home-hero-banner img {{
            width: 100%;
            max-width: 100%;
            height: auto;
            display: block;
            vertical-align: middle;
        }}

        /* Pills */
        .pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0 1.5rem 0;
        }}
        .pill {{
            background: {CARD_ELEVATED};
            color: {TEXT};
            border: 1px solid #3e3e3e;
            border-radius: 999px;
            padding: 0.35rem 1rem;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.08em;
        }}

        .tagline-footer {{
            text-align: center;
            color: {ACCENT};
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            margin: 2rem 0 1rem 0;
            font-weight: 600;
        }}
        .tagline-footer .dash {{ color: {ACCENT_RED}; }}

        .status-chip {{
            background: {CARD};
            border: 1px solid #282828;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }}

        .metric-card, [data-testid="stMetric"] {{
            background: {CARD};
            border-radius: 8px;
            padding: 0.5rem;
        }}
        .metric-card h4 {{
            color: {ACCENT} !important;
            margin: 0 0 0.5rem 0;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
        }}

        .editorial-takeaway {{
            background: {CARD};
            border-left: 3px solid {ACCENT};
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin-top: 1.5rem;
        }}
        .editorial-takeaway li {{ color: {MUTED}; margin-bottom: 0.35rem; }}

        .quote-card {{
            background: {CARD_ELEVATED};
            border-left: 4px solid {ACCENT_RED};
            padding: 1.25rem 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: {MUTED};
            line-height: 1.6;
        }}

        .role-chip {{
            display: inline-block;
            background: #333;
            color: {ACCENT};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .footer-note {{
            color: {MUTED};
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #282828;
        }}

        .stButton > button[kind="primary"],
        .stButton > button {{
            background-color: {ACCENT} !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 999px !important;
            font-weight: 600 !important;
        }}
        .stButton > button:hover {{
            background-color: #1fdf64 !important;
            color: #000 !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: {ACCENT} !important;
            font-weight: 700;
        }}
        [data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: #282828 !important;
            background: {BG_ELEVATED};
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        f'<div class="footer-note">{FOOTER_TAGLINE}<br><em>{DISCLAIMER}</em></div>',
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str):
    st.markdown(f"## {title}")
    st.caption(description)


def editorial_takeaway(bullets: list[str]):
    st.markdown("### Editorial Takeaway")
    html = '<div class="editorial-takeaway"><ul>'
    for b in bullets:
        html += f"<li>{b}</li>"
    html += "</ul></div>"
    st.markdown(html, unsafe_allow_html=True)
