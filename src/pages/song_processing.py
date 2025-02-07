import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception

def process_song(file):
    """Uploads a song to the backend for processing into Clone Hero format."""
    try:
        files = {"file": file}
        with st.progress(20, text="Uploading song..."):
            response = requests.post(f"{API_URL}/process_song/", files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to process song: {e}")
        return {"error": str(e)}

def song_processing_page():
    """Streamlit UI for processing songs into Clone Hero format."""
    st.title("🎸 Clone Hero Song Processor")
    st.write("Upload a song file, and we'll process it into Clone Hero format!")

    # Upload song file
    st.header("📤 Upload a Song for Processing")
    uploaded_file = st.file_uploader(
        "Choose a song file (mp3, wav, opus, flac, ogg)", 
        type=["mp3", "wav", "opus", "flac", "ogg"]
    )

    if uploaded_file:
        st.write(f"**Processing:** {uploaded_file.name}")
        with st.spinner("Analyzing audio and generating notes..."):
            result = process_song(uploaded_file)

        if "error" in result:
            st.error(f"🚨 Error processing song: {result['error']}")
            display_exception(result["error"])
        else:
            st.success("✅ Song processed successfully!")
            st.write(f"🎵 **Generated Notes Chart:** `{result.get('notes_chart', 'N/A')}`")
            st.write(f"🎶 **Detected Tempo:** `{result.get('tempo', 'Unknown')} BPM`")
            st.download_button(
                "⬇️ Download notes.chart",
                data=requests.get(result["notes_chart"]).content,
                file_name="notes.chart",
                mime="text/plain"
            )

    st.markdown("---")
    st.subheader("📖 How It Works")
    st.write("""
    1️⃣ Upload a song file (MP3, WAV, OPUS, FLAC, OGG).  
    2️⃣ The system analyzes the song, detects tempo, and generates notes.  
    3️⃣ Download the generated `notes.chart` file for Clone Hero!  
    """)

    st.info("💡 Need help? Ensure the file format is correct and try again.")