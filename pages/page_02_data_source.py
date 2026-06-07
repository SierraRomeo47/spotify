"""Spotify connection — sidebar status and optional refresh."""

import streamlit as st

from config import EXPORTIFY_PLAYLISTS_DIR, MY_SPOTIFY_DATA_DIR, SPOTIFY_ACCOUNT_DATA_DIR
from exportify_loader import clear_exportify_bundle_cache
from spotify_account_loader import account_data_available, clear_account_bundle_cache
from spotify_auth import check_credentials, clear_cache
from session_state import bootstrap_data, fetch_all_spotify_data, load_from_uploads


def _exportify_status_caption():
    stats = st.session_state.get("exportify_stats") or {}
    master = st.session_state.get("exportify_master")
    n_master = len(master) if master is not None and not master.empty else 0
    n_pl = len(st.session_state.get("playlist_tracks") or {})
    parts = [f"enrichment tracks: **{n_master}**", f"playlists: **{n_pl}**"]
    if stats.get("streaming_plays"):
        parts.append(f"streaming plays: **{stats.get('streaming_plays')}**")
    if stats:
        parts.append(f"liked: **{stats.get('liked_tracks', 0)}**")
    return " · ".join(parts)


def render_data_connect_expander():
    """Data status and optional refresh — lives in sidebar."""
    with st.expander("Data source", expanded=False):
        source = st.session_state.get("data_source", "none")
        profile = st.session_state.get("user_profile", {})
        boot_at = st.session_state.get("bootstrap_at", "")
        enrich_status = st.session_state.get("genre_enrichment_status", "")

        st.caption(f"Source: **{source}** · User: **{profile.get('display_name', '—')}**")
        if boot_at:
            st.caption(f"Last bootstrap: {boot_at[:19].replace('T', ' ')} UTC")

        if source in ("exportify", "api+exportify", "account", "account+exportify", "account+api", "account+exportify+api"):
            st.caption(_exportify_status_caption())
            st.caption(
                "Primary source: **my_spotify_data/** privacy export. "
                "Exportify CSVs in spotify_playlists/ add genres and audio features when present."
            )

        if enrich_status:
            st.caption(f"Genre enrichment: {enrich_status}")

        messages = st.session_state.get("bootstrap_messages") or []
        for msg in messages:
            if "add SPOTIPY" in msg or "no CSVs" in msg:
                st.warning(msg)
            elif msg.startswith("Exportify:") or msg.startswith("Spotify:"):
                st.info(msg)

        if not st.session_state.get("data_bootstrap_complete"):
            st.info("Loading library on startup…")

        st.caption(
            "Vercel portfolio: run `python scripts/build_site_data.py` after refreshing data."
        )

        has_creds = check_credentials()

        if has_creds:
            if st.button("Refresh Spotify data", use_container_width=True):
                with st.spinner("Refreshing API data…"):
                    errors = fetch_all_spotify_data(
                        open_browser=False,
                        skip_exportify_reload=True,
                    )
                if errors:
                    for e in errors:
                        st.warning(e)
                else:
                    st.success("Spotify data refreshed.")
                st.rerun()
        else:
            st.caption("Add SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET to `.env` for live API.")

        if account_data_available() or (
            EXPORTIFY_PLAYLISTS_DIR.exists() and any(EXPORTIFY_PLAYLISTS_DIR.glob("*.csv"))
        ):
            if st.button("Reload local library", use_container_width=True):
                clear_exportify_bundle_cache()
                clear_account_bundle_cache()
                with st.spinner("Reloading my_spotify_data…"):
                    bootstrap_data(force=True)
                st.success("Local library reloaded.")
                st.rerun()

        if st.button("Re-run full bootstrap", use_container_width=True):
            with st.spinner("Bootstrap…"):
                errors = bootstrap_data(force=True)
            if errors:
                for e in errors:
                    st.warning(e)
            st.success("Bootstrap complete.")
            st.rerun()

        if st.button("Clear token cache", use_container_width=True):
            clear_cache()
            st.info("Token cache cleared. Re-run bootstrap to re-authenticate.")

        with st.expander("Upload CSV exports (advanced)"):
            st.caption("Optional: upload Spotify or Exportify-shaped CSV exports.")
            tracks_f = st.file_uploader("Top tracks", type=["csv"], key="up_tracks")
            artists_f = st.file_uploader("Top artists", type=["csv"], key="up_artists")
            recent_f = st.file_uploader("Recently played", type=["csv"], key="up_recent")
            playlists_f = st.file_uploader("Playlists", type=["csv"], key="up_playlists")
            if st.button("Apply uploads", use_container_width=True):
                load_from_uploads(tracks_f, artists_f, recent_f, playlists_f)
                st.rerun()


def render():
    render_data_connect_expander()
