import os
import sys
import streamlit as st
from loguru import logger
import requests

# Configure Loguru logging
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "streamlit_app.log")
logger.add(LOG_FILE, rotation="10MB", retention=5, compression="zip", level="DEBUG")

# Enable console logging only in development mode
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    logger.add(sys.stdout, level="DEBUG")

# The base API URL for your FastAPI app, configurable via environment variable
API_URL = os.getenv("API_URL", "http://clonehero_api:8000")

def make_api_request(endpoint: str, method="GET", data=None, files=None, params=None):
    """
    Handles API requests with better error handling.
    
    Args:
        endpoint (str): API endpoint (e.g., "songs/")
        method (str): HTTP method (GET, POST, PUT, DELETE)
        data (dict, optional): JSON data payload for POST/PUT
        files (dict, optional): Files for multipart uploads
        params (dict, optional): Query parameters for GET requests

    Returns:
        dict: Response JSON or an error message.
    """
    url = f"{API_URL}/{endpoint}"
    try:
        headers = {"Accept": "application/json"}
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            files=files,
            params=params,
            timeout=60 if method.upper() == "POST" else 30
        )
        
        response.raise_for_status()
        return response.json()
    
    except requests.Timeout:
        logger.error(f"API request timeout: {method} {url}")
        return {"error": "Request timed out. Please try again."}
    
    except requests.RequestException as e:
        logger.error(f"API request failed: {method} {url} - {e}")
        return {"error": f"API request failed: {str(e)}"}

def display_exception(e, user_msg: str):
    """
    Log and display an error from an exception in Streamlit.
    Shows a generic message in production for security.
    
    Args:
        e (Exception): The exception object.
        user_msg (str): User-friendly message to display.
    """
    logger.exception(f"{user_msg}: {str(e)}")
    
    if DEBUG_MODE:
        st.error(f"{user_msg}: {str(e)}")  # Show detailed error in debug mode
    else:
        st.error(user_msg)  # Generic error message for production
    
    st.toast("❌ An error occurred. Please check logs for details.", icon="⚠️")