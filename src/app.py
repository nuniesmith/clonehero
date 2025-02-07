import streamlit as st
from loguru import logger
from src.pages.song_processing import song_processing_page
from src.pages.song_upload import song_upload_page
from src.pages.database_explorer import database_explorer_page
from src.pages.colors import colors_page
from src.pages.backgrounds import backgrounds_page
from src.pages.highways import highways_page

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Clone Hero Manager",
    page_icon="assets/ch_icon.png",
    layout="wide"
)

st.sidebar.image("assets/ch_icon.png", width=50)
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio(
    "Select a Page",
    [
        "Database Explorer",
        "Upload Songs",
        "Generate Songs",
        "Colors",
        "Backgrounds",
        "Highways",
    ]
)

if menu_selection == "Database Explorer":
    database_explorer_page()
elif menu_selection == "Upload Songs":
    song_upload_page()
elif menu_selection == "Generate Songs":
    song_processing_page()
elif menu_selection == "Colors":
    colors_page()
elif menu_selection == "Backgrounds":
    backgrounds_page()
elif menu_selection == "Highways":
    highways_page()
else:
    st.error("Invalid selection.")