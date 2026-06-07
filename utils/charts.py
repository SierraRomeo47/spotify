"""Plotly chart helpers — Spotify-inspired dark theme."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import ACCENT, ACCENT_RED, BG, CARD, CARD_ELEVATED, MUTED, TEXT

CHART_COLORS = [ACCENT, "#ffffff", ACCENT_RED, "#535353", "#b3b3b3", "#6c5ce7", "#fdcb6e"]


def apply_spotify_layout(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT, size=16, family="Arial Black, sans-serif")),
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font=dict(color=TEXT, size=12),
        legend=dict(bgcolor=CARD, font=dict(color=TEXT), orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=48, r=24, t=72 if title else 48, b=48),
        xaxis=dict(gridcolor="#282828", zerolinecolor="#282828", tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor="#282828", zerolinecolor="#282828", tickfont=dict(color=MUTED)),
        hoverlabel=dict(bgcolor=CARD_ELEVATED, font_color=TEXT),
    )
    return fig


# Backward compatibility
def plotly_dark_layout(fig: go.Figure, title: str = "") -> go.Figure:
    return apply_spotify_layout(fig, title)


def metric_for_chart(df: pd.DataFrame, prefer: str = "popularity") -> tuple[str, str]:
    """
    Pick chart metric column and axis label.
    Falls back to inverted rank when popularity is unavailable (dev API).
    """
    if df is None or df.empty:
        return "rank", "Rank (lower = higher)"

    if prefer in df.columns:
        series = pd.to_numeric(df[prefer], errors="coerce")
        if series.notna().any():
            return prefer, prefer.replace("_", " ").title()

    if "rank" in df.columns:
        df = df.copy()
        df["_chart_score"] = 21 - pd.to_numeric(df["rank"], errors="coerce").fillna(20)
        return "_chart_score", "Taste weight (from rank)"

    if "followers" in df.columns:
        return "followers", "Followers"

    return "rank", "Rank"


def prepare_chart_df(df: pd.DataFrame, prefer: str = "popularity") -> tuple[pd.DataFrame, str, str]:
    """Return dataframe with chart value column ready."""
    if df is None or df.empty:
        return df, prefer, prefer
    out = df.copy()
    col, label = metric_for_chart(out, prefer)
    if col == "_chart_score" and "_chart_score" not in out.columns and "rank" in out.columns:
        out["_chart_score"] = 21 - pd.to_numeric(out["rank"], errors="coerce").fillna(20)
    return out, col, label


def rank_bar_chart(
    df: pd.DataFrame,
    name_col: str,
    value_col: str | None = None,
    title: str = "",
    prefer_metric: str = "popularity",
    top_n: int = 20,
) -> go.Figure:
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False, font=dict(color=MUTED))
        return apply_spotify_layout(fig, title)

    subset = df.head(top_n).copy()
    subset, col, x_label = prepare_chart_df(subset, prefer_metric)
    if value_col:
        col = value_col

    subset = subset.sort_values(col, ascending=True)
    fig = px.bar(
        subset,
        x=col,
        y=name_col,
        orientation="h",
        title=title,
        color_discrete_sequence=[ACCENT],
    )
    fig.update_layout(xaxis_title=x_label, yaxis_title="")
    fig.update_traces(marker_line_width=0)
    return apply_spotify_layout(fig, title)


def donut_chart(labels, values, title: str = "") -> go.Figure:
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=CHART_COLORS),
                textfont=dict(color=TEXT),
            )
        ]
    )
    return apply_spotify_layout(fig, title)


def bar_chart_simple(x, y, title: str = "", x_title: str = "", y_title: str = "") -> go.Figure:
    fig = px.bar(x=x, y=y, title=title, color_discrete_sequence=[ACCENT])
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    fig.update_traces(marker_line_width=0)
    return apply_spotify_layout(fig, title)


def popularity_footnote(df: pd.DataFrame) -> str | None:
    if df is None or df.empty or "popularity" not in df.columns:
        return None
    pop = pd.to_numeric(df["popularity"], errors="coerce")
    if pop.notna().any():
        return None
    return "Track popularity unavailable from API (Development mode). Charts use rank-based weight instead."
