import streamlit as st
import requests
from loguru import logger
from src.pages.song_processing import song_processing_page
from src.pages.song_manager import song_manager_page
from src.pages.database_explorer import database_explorer_page
from src.pages.colors import colors_page
from src.pages.backgrounds import backgrounds_page
from src.pages.highways import highways_page
from src.utils import API_URL

# App Configuration
st.set_page_config(
    page_title="Clone Hero Manager",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar - App Branding & Theme Toggle
def setup_sidebar():
    """Define sidebar UI elements only once."""
    st.sidebar.image("assets/ch_icon.png", width=60)
    st.sidebar.title("🎸 Clone Hero Manager")
    st.sidebar.markdown("---")

    # API Connection Status
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        api_status = "🟢 API Online" if response.status_code == 200 else "🔴 API Offline"
    except requests.RequestException:
        api_status = "🔴 API Offline"

    st.sidebar.write(f"**Status:** {api_status}")

    # Navigation Menu
    PAGES = {
        "📁 Database Explorer": database_explorer_page,
        "📤 Upload Songs": song_manager_page,
        "🎵 Generate Songs": song_processing_page,
        "🎨 Colors": colors_page,
        "🌆 Backgrounds": backgrounds_page,
        "🛣️ Highways": highways_page,
    }
    
    menu_selection = st.sidebar.radio("📌 Select a Page", list(PAGES.keys()))

    st.sidebar.markdown("---")
    st.sidebar.write("🛠️ **Clone Hero Manager** - v1.0.0")
    st.sidebar.write("🚀 Developed with ❤️ using Streamlit")

    return PAGES[menu_selection]

# Call the function once, ensuring sidebar elements don’t get duplicated
selected_page = setup_sidebar()

# Render the selected page
selected_page()