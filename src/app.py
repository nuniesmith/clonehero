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

# API Connection Status (primary service)
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    if response.status_code == 200:
        api_status = "🟢 Online"
    else:
        api_status = "🔴 Offline"
except requests.RequestException as e:
    api_status = "🔴 Offline"
    logger.error(f"❌ Failed to connect to API: {e}")

# Additional Service Health Check Function
def check_service(endpoint):
    try:
        resp = requests.get(f"{API_URL}/{endpoint}", timeout=5)
        if resp.status_code == 200:
            return "🟢 Online"
        return "🔴 Offline"
    except requests.RequestException as e:
        logger.error(f"❌ {endpoint} check failed: {e}")
        return "🔴 Offline"

# Check other services
service_statuses = {
    "API": api_status,
    "Backend": check_service("backend"),
    "Database": check_service("database"),
    "Sync": check_service("sync"),
}

# Visualize service statuses on the main page
st.markdown("## System Health")
cols = st.columns(len(service_statuses))
for idx, (service, status) in enumerate(service_statuses.items()):
    cols[idx].metric(label=service, value=status)

# Sidebar - App Branding, Status, & Navigation
def setup_sidebar(api_status):
    """Define sidebar UI elements only once."""
    # App Branding
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

    # API Status
    st.sidebar.write(f"**Status:** {api_status}")

    # Refresh & Clear Cache Buttons
    if st.sidebar.button("🔄 Refresh App"):
        st.experimental_rerun()
    
    if st.sidebar.button("♻️ Clear Cache"):
        st.cache_data.clear()
        st.experimental_rerun()

    st.sidebar.markdown("---")

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

# Render Sidebar Navigation
selected_page = setup_sidebar(api_status)

# Render the selected page
selected_page()