import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL

def fetch_songs(search_query=None):
    """Fetch all songs from the database with optional search filtering."""
    try:
        params = {"search_query": search_query} if search_query else {}
        response = requests.get(f"{API_URL}/songs/", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch songs: {e}")
        return {"error": str(e)}

def delete_song(song_id):
    """Delete a song from the database."""
    try:
        response = requests.delete(f"{API_URL}/songs/{song_id}", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to delete song: {e}")
        return {"error": str(e)}

def database_explorer_page():
    """Streamlit page to explore, search, and delete songs from the database."""
    st.title("📁 Song Database Explorer")

    # Search bar
    search_query = st.text_input("🔍 Search for a song (by title, artist, or album)", "")
    
    if st.button("Search"):
        with st.spinner("Searching..."):
            songs = fetch_songs(search_query)
    else:
        songs = fetch_songs()
    
    if "error" in songs:
        st.error(f"Error fetching songs: {songs['error']}")
        return

    if not songs:
        st.info("No songs found in the database.")
        return
    
    for song in songs:
        with st.expander(f"🎵 {song.get('title', 'Unknown Title')} - {song.get('artist', 'Unknown Artist')}"):
            st.write(f"**Album:** {song.get('album', 'Unknown')}")
            st.write(f"**File Path:** {song.get('file_path', 'N/A')}")
            metadata = song.get("metadata", {})
            if metadata:
                st.json(metadata, expanded=False)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Delete {song.get('title', 'this song')}", key=f"delete_{song['id']}"):
                    with st.spinner("Deleting song..."):
                        result = delete_song(song['id'])
                    if "error" in result:
                        st.error(f"Error deleting song: {result['error']}")
                    else:
                        st.success("Song deleted successfully!")
                        st.rerun()