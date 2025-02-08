import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL

# Constants
PAGE_SIZE = 10  # Number of songs per page

@st.cache_data(ttl=30)
def fetch_songs(search_query=None, limit=PAGE_SIZE, offset=0):
    """Fetch all songs from the database with optional search filtering and pagination."""
    try:
        params = {"search": search_query, "limit": limit, "offset": offset}
        response = requests.get(f"{API_URL}/songs/", params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("songs", [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch songs: {e}")
        return []

def delete_song(song_id):
    """Delete a song from the database."""
    try:
        response = requests.delete(f"{API_URL}/songs/{song_id}", timeout=30)
        response.raise_for_status()
        return {"success": True}
    except requests.RequestException as e:
        logger.error(f"Failed to delete song: {e}")
        return {"error": str(e)}

def database_explorer_page():
    """Streamlit page to explore, search, and delete songs from the database."""
    st.title("📁 Song Database Explorer")
    st.write("Manage and explore the Clone Hero song database.")

    # Initialize Session State for Pagination
    if "page" not in st.session_state:
        st.session_state.page = 0

    # Search and Pagination State
    search_query = st.text_input("🔍 Search for a song (title, artist, album)", "")

    # Reset pagination when a new search is performed
    if search_query != st.session_state.get("last_search", ""):
        st.session_state.page = 0
        st.session_state.last_search = search_query

    # Fetch Songs
    songs = fetch_songs(search_query, limit=PAGE_SIZE, offset=st.session_state.page * PAGE_SIZE)

    if not songs:
        st.warning("⚠️ No songs found in the database.")
        return

    # Song Listing
    for song in songs:
        with st.expander(f"🎵 {song.get('title', 'Unknown Title')} - {song.get('artist', 'Unknown Artist')}"):
            st.write(f"**Album:** {song.get('album', 'Unknown')}")
            st.write(f"**File Path:** `{song.get('file_path', 'N/A')}`")

            # Show Metadata if available
            metadata = song.get("metadata", {})
            if metadata:
                non_empty_metadata = {k: v for k, v in metadata.items() if v}  # Hide empty fields
                if non_empty_metadata:
                    with st.expander("🔎 View Metadata"):
                        st.json(non_empty_metadata, expanded=False)

            # Delete Button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{song['id']}"):
                    with st.spinner("Deleting song..."):
                        result = delete_song(song["id"])
                    if "error" in result:
                        st.error(f"❌ Error deleting song: {result['error']}")
                    else:
                        st.success("✅ Song deleted successfully!")
                        st.rerun()

    # Pagination Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.page == 0):
            st.session_state.page = max(st.session_state.page - 1, 0)
            st.rerun()
    with col3:
        if st.button("Next ➡️", disabled=len(songs) < PAGE_SIZE):
            st.session_state.page += 1
            st.rerun()

    # Divider
    st.markdown("---")

    ### **📖 How It Works Section**
    st.subheader("📖 How It Works")
    st.write(
        """
        ### **Step-by-Step Guide**
        1️⃣ **Search for a Song**
           - Use the **search bar** to find songs by **title, artist, or album**.  
           - Supports **partial matches** (e.g., searching "Metal" will find "Metallica").  
        
        2️⃣ **View Song Details**
           - Click on a song to **expand its metadata**.  
           - See its **title, artist, album, file path, and additional metadata**.  
        
        3️⃣ **Delete a Song (Admin Only)**
           - Click **🗑️ Delete** to remove a song from the database.  
           - **⚠️ This action is permanent and cannot be undone!**  

        ### **🔍 Features**
        ✅ **Search and Filter Songs**  
        ✅ **Pagination Support** - Browse through **large song libraries**.  
        ✅ **View Full Metadata** for each song.  
        ✅ **Admin Controls** - **Delete unwanted songs** with a single click.  

        ### **🛠️ When to Use This?**
        - **Curate your Clone Hero library** by removing unwanted songs.  
        - **Fix metadata issues** by viewing song details.  
        - **Check uploaded song paths** for troubleshooting.  
        """
    )

    st.info("💡 Need help? Try searching by artist name, album, or song title.")