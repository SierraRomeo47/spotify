"""
Sierra Romeo Editorial Intelligence Lab
Minimal employer-focused portfolio — 5 pages.
"""

import streamlit as st

from config import APP_SUBTITLE, APP_TITLE, ROLE_WORKFLOW
from session_state import init_session
from ui.theme import inject_custom_css, render_footer

from pages.page_01_profile import render as render_home
from pages.page_02_data_source import render_data_connect_expander
from pages.page_discovery import render as render_discovery
from pages.page_culture import render as render_culture
from pages.page_curate import render as render_curate
from pages.page_10_role_fit import render as render_role_fit

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()
init_session()

st.sidebar.markdown(f"## {APP_TITLE}")
st.sidebar.caption(APP_SUBTITLE)
st.sidebar.caption(f"*{ROLE_WORKFLOW}*")
st.sidebar.markdown("---")
st.sidebar.caption(f"Data: **{st.session_state.get('data_source', '—')}**")
render_data_connect_expander()
st.sidebar.markdown("---")

try:
    pg = st.navigation(
        [
            st.Page(render_home, title="Home", icon="👤", url_path="home"),
            st.Page(render_discovery, title="Discovery", icon="📡", url_path="discovery"),
            st.Page(render_culture, title="Culture & lanes", icon="🌍", url_path="culture"),
            st.Page(render_curate, title="Curate", icon="🎚️", url_path="curate"),
            st.Page(render_role_fit, title="Role Fit", icon="📄", url_path="role-fit", default=True),
        ],
        position="sidebar",
    )
    pg.run()
except AttributeError:
    choice = st.sidebar.radio(
        "Navigate",
        ["Home", "Discovery", "Culture & lanes", "Curate", "Role Fit"],
        index=4,
    )
    routes = {
        "Home": render_home,
        "Discovery": render_discovery,
        "Culture & lanes": render_culture,
        "Curate": render_curate,
        "Role Fit": render_role_fit,
    }
    routes[choice]()

render_footer()
