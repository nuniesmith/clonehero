import streamlit as st
import requests
from loguru import logger
from src.pages.song_processing import song_processing_page
from src.pages.song_upload import song_upload_page
from src.pages.database_explorer import database_explorer_page
from src.pages.colors import colors_page
from src.pages.backgrounds import backgrounds_page
from src.pages.highways import highways_page
import os

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# App Configuration
st.set_page_config(
    page_title="Clone Hero Manager",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Toggle (Stores in Session State)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def toggle_dark_mode():
    """Switches between light and dark mode."""
    st.session_state.dark_mode = not st.session_state.dark_mode

# Custom CSS for Dark Mode
DARK_MODE_CSS = """
<style>
    body, .stApp {
        background-color: #121212 !important;
        color: white !important;
    }
    .stSidebar {
        background-color: #1E1E1E !important;
    }
    .stButton>button {
        background-color: #6200EE !important;
        color: white !important;
    }
    .stRadio div[role="radiogroup"] label {
        color: white !important;
    }
</style>
"""

# Apply Dark Mode CSS if Enabled
if st.session_state.dark_mode:
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)

# Sidebar - App Branding & Theme Toggle
st.sidebar.image("assets/ch_icon.png", width=60)
st.sidebar.title("🎸 Clone Hero Manager")
st.sidebar.markdown("---")

# Dark Mode Toggle Button
if st.sidebar.button("🌓 Toggle Dark Mode"):
    toggle_dark_mode()
    st.rerun()

# API Connection Status
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    api_status = "🟢 API Online" if response.status_code == 200 else "🔴 API Offline"
except requests.RequestException:
    api_status = "🔴 API Offline"

st.sidebar.write(f"**Status:** {api_status}")

# Navigation Dictionary for Clean Code
PAGES = {
    "📁 Database Explorer": database_explorer_page,
    "📤 Upload Songs": song_upload_page,
    "🎵 Generate Songs": song_processing_page,
    "🎨 Colors": colors_page,
    "🌆 Backgrounds": backgrounds_page,
    "🛣️ Highways": highways_page,
}

# Sidebar - Navigation
menu_selection = st.sidebar.radio("📌 Select a Page", list(PAGES.keys()))

# Render the Selected Page
PAGES[menu_selection]()  

# Footer
st.sidebar.markdown("---")
st.sidebar.write("🛠️ **Clone Hero Manager** - v1.0.0")
st.sidebar.write("🚀 Developed with ❤️ using Streamlit")