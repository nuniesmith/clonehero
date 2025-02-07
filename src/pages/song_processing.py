import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception

def process_song(file):
    """Uploads a song to the backend for processing into Clone Hero format."""
    try:
        files = {"file": file}
        response = requests.post(f"{API_URL}/process_song/", files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to process song: {e}")
        return {"error": str(e)}

def song_processing_page():
    """Streamlit UI for processing songs into Clone Hero format."""
    st.title("🎸 Clone Hero Song Processor")

    # Upload song file
    st.header("📤 Upload a Song for Processing")
    uploaded_file = st.file_uploader("Choose a song file (mp3, wav, opus)", type=["mp3", "wav", "opus"])

    if uploaded_file:
        st.write(f"Processing: {uploaded_file.name}")
        with st.spinner("Processing song..."):
            result = process_song(uploaded_file)

        if "error" in result:
            st.error(f"Error processing song: {result['error']}")
        else:
            st.success("Song processed successfully!")
            st.write(f"**Generated Notes Chart:** {result.get('notes_chart', 'N/A')}")
            st.write(f"**Detected Tempo:** {result.get('tempo', 'Unknown')}")