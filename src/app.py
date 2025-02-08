import streamlit as st
import requests
from loguru import logger
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import page components
from src.pages.song_processing import song_processing_page
from src.pages.song_manager import song_manager_page
from src.pages.database_explorer import database_explorer_page
from src.pages.colors import colors_page
from src.pages.backgrounds import backgrounds_page
from src.pages.highways import highways_page

# Read API URL from environment variable
API_URL = os.getenv("API_URL", "http://clonehero_api:8000")

# Configure Streamlit App
st.set_page_config(
    page_title="Clone Hero Manager",
    page_icon="assets/ch_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar - App Branding & Theme Toggle
def setup_sidebar():
    """Define sidebar UI elements only once."""
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="assets/ch_icon.png" width="50">
            <h2 style="margin: 0;">Clone Hero Manager</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # API Connection Status
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            api_status = "🟢 API Online"
        else:
            api_status = "🔴 API Offline"
    except requests.RequestException as e:
        api_status = "🔴 API Offline"
        logger.error(f"❌ Failed to connect to API: {e}")

    st.sidebar.write(f"**Status:** {api_status}")

    # Refresh & Clear Cache Buttons
    if st.sidebar.button("🔄 Refresh App"):
        st.experimental_rerun()
    
    if st.sidebar.button("♻️ Clear Cache"):
        st.cache_data.clear()
        st.experimental_rerun()

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