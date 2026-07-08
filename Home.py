"""StreetNets entrypoint.

Run with: streamlit run Home.py

This file only configures the app and routes between pages via st.navigation,
so every page gets a proper title/icon in the sidebar and shares the same
chrome. Page content lives in the pages/ folder.
"""

import streamlit as st

st.set_page_config(
    page_title="StreetNets | No-Code Network Analysis",
    page_icon="🛣️",
    layout="wide",
)

# Shared chrome: hide Streamlit's menu, footer and deploy button, but keep the
# header so the sidebar toggle is always reachable.
st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stAppDeployButton {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

pages = [
    st.Page("pages/Landing.py", title="Home", icon="🏠", default=True),
    st.Page("pages/Retrieve_city_data.py", title="Retrieve City Data", icon="📊"),
    st.Page("pages/Database.py", title="City Database", icon="🗺️"),
    st.Page("pages/Glossary.py", title="Glossary", icon="📖"),
]

st.navigation(pages).run()
