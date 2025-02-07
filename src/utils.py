import os
import sys
import streamlit as st
from loguru import logger
import requests

# Configure Loguru logging
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "streamlit_app.log")
logger.add(LOG_FILE, rotation="10MB", retention=5, compression="zip", level="DEBUG")

# Enable console logging only in development mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    logger.add(sys.stdout, level="DEBUG")

# The base API URL for your FastAPI app, configurable via environment variable
API_URL = os.getenv("API_URL", "http://clonehero_api:8000")

def make_api_request(endpoint: str, method="GET", data=None, files=None):
    """Handles API requests with better error handling."""
    url = f"{API_URL}/{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, files=files, timeout=60)
        else:
            raise ValueError("Unsupported HTTP method")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"error": str(e)}

def display_exception(e, user_msg: str):
    """
    Log and display an error from an exception in Streamlit.
    Shows a generic message in production for security.
    """
    logger.exception(f"{user_msg}: {str(e)}")
    if DEBUG_MODE:
        st.error(f"{user_msg}: {str(e)}")  # Show detailed error in debug mode
    else:
        st.error(f"{user_msg}: Something went wrong. Please try again later.")