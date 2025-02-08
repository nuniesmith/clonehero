import streamlit as st
import os
from dotenv import load_dotenv
from src.health_check import get_service_statuses, clear_service_cache
from src.sidebar import setup_sidebar

# Load environment variables
load_dotenv()

NGINX_URL = "http://clonehero_nginx"

API_URL = f"{NGINX_URL}/api"
DATABASE_URL = f"{NGINX_URL}/database"

# Configure Streamlit App
st.set_page_config(
    page_title="Clone Hero Manager",
    page_icon="assets/ch_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Render Sidebar Navigation with health status
service_statuses = get_service_statuses(API_URL, DATABASE_URL)
selected_page = setup_sidebar(service_statuses)

# Render the selected page
selected_page()