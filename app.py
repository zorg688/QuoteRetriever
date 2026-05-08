import streamlit as st

pg = st.navigation([
    st.Page("app_page_quotes.py", title="Quote Retriever", icon="📖"),
    st.Page("app_page_steam.py", title = "Game Recomender", icon = "🎮")
])
pg.run()