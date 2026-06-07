"""Page 1: Home — minimal editorial positioning."""

import streamlit as st

from config import DEFAULT_DJ_STORY, PROFILE_ROLE_PILLS
from ui.components import home_hero_banner, pill_row, profile_tagline_footer


def render():
    home_hero_banner()
    pill_row(PROFILE_ROLE_PILLS)

    st.markdown(
        """
**Spotify Editor, Music & Culture (International & Hip-Hop) · Mumbai**

- **Discovery** — spot emerging artists before long-term adoption (listen velocity + day-by-day plays).
- **Culture & lanes** — programme India ↔ global hip-hop and club/electronic crossovers from real taste.
- **Curate** — sequenced playlists with editorial voice; **Role Fit** — JD-mapped summary tied to my CV (ShipWatch analytics, FPL app, DJ practice, Maersk/IIM).
        """
    )

    with st.expander("Your DJ story"):
        st.session_state["dj_story"] = st.text_area(
            "Editable narrative",
            value=st.session_state.get("dj_story", DEFAULT_DJ_STORY),
            height=120,
            label_visibility="collapsed",
        )

    profile_tagline_footer()
