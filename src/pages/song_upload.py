import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception
import itertools

@st.cache_data(ttl=300)
def fetch_songs():
    """Fetch song list from the API and return it."""
    try:
        logger.info("Fetching song list from API.")
        response = requests.get(f"{API_URL}/songs/", timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and "songs" in data:
            songs = data["songs"]
        elif isinstance(data, list):
            songs = data
        else:
            logger.error(f"Unexpected API response format: {data}")
            return []
        
        logger.success(f"Fetched {len(songs)} songs from the database.")
        return songs
    except requests.RequestException as e:
        logger.error(f"Failed to fetch songs: {e}")
        st.error("Error fetching songs. Please try again later.")
        return []

def display_songs():
    """Display songs grouped by artist and album."""
    songs = fetch_songs()
    if not songs:
        st.info("No songs found in the library.")
        return
    
    st.subheader("Song Library")
    songs.sort(key=lambda s: (s.get('artist', 'N/A').lower(),
                              s.get('album', 'N/A').lower(),
                              s.get('title', 'N/A').lower()))
    
    for artist, artist_group in itertools.groupby(songs, key=lambda s: s.get('artist', 'N/A')):
        st.markdown(f"## 🎸 {artist}")
        artist_songs = list(artist_group)
        for album, album_group in itertools.groupby(artist_songs, key=lambda s: s.get('album', 'N/A')):
            st.markdown(f"### 📀 {album}")
            for song in album_group:
                with st.container():
                    st.markdown(f"**🎵 Title:** {song.get('title', 'N/A')}")
                    st.write(f"📁 **Folder Path:** {song.get('file_path', 'N/A')}")
                    metadata = song.get("metadata", {})
                    if metadata:
                        with st.expander("Show Metadata"):
                            st.json(metadata, expanded=False)
                st.write("---")

def song_upload_page():
    """Streamlit UI for uploading, downloading, and listing songs."""
    st.title("🎶 Clone Hero Manager - Songs")
    
    st.header("📤 Upload a Song")
    uploaded_file = st.file_uploader("Choose a .zip or .rar file", type=["zip", "rar"])
    
    if uploaded_file:
        try:
            TEN_GB = 10 * 1024 * 1024 * 1024
            if uploaded_file.size > TEN_GB:
                st.error("File size exceeds 10GB limit.")
                return
            
            logger.info(f"Uploading file: {uploaded_file.name}")
            files = {"file": uploaded_file}
            data = {"content_type": "songs"}
            
            with st.spinner("Uploading song..."):
                response = requests.post(f"{API_URL}/upload_content/", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                resp_json = response.json()
                if "error" in resp_json:
                    st.error(f"Upload error: {resp_json['error']}")
                    logger.error(f"Upload error: {resp_json['error']}")
                else:
                    st.success(resp_json.get("message", "Song(s) uploaded successfully!"))
                    logger.success(f"Successfully uploaded: {uploaded_file.name}")
                    display_songs()
            else:
                st.error(f"Upload failed: {response.text}")
                logger.error(f"Upload failed: {uploaded_file.name}, Status Code: {response.status_code}")
        except Exception as e:
            display_exception(e, f"An error occurred while uploading {uploaded_file.name}")
    
    st.header("📥 Download a Song via URL")
    song_url = st.text_input("Enter song download URL (zip/rar)")
    
    if st.button("Download"):
        if song_url:
            try:
                logger.info(f"Downloading from URL: {song_url}")
                with st.spinner("Downloading song..."):
                    response = requests.post(f"{API_URL}/download/", json={"url": song_url}, timeout=30)
                if response.status_code == 200:
                    resp_json = response.json()
                    if "error" in resp_json:
                        st.error(f"Download error: {resp_json['error']}")
                        logger.error(f"Download error: {resp_json['error']}")
                    else:
                        st.success(resp_json.get("message", "Song downloaded successfully!"))
                        logger.success(f"Downloaded successfully from: {song_url}")
                        display_songs()
                else:
                    st.error(f"Download failed: {response.text}")
                    logger.error(f"Download failed from {song_url}, Status Code: {response.status_code}")
            except Exception as e:
                display_exception(e, f"An error occurred while downloading from {song_url}")
        else:
            st.warning("Please enter a valid URL.")
    
    st.header("🎼 Current Song Library")
    display_songs()