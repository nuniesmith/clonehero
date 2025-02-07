import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception

# Allowed file types
FILE_EXTENSIONS = {
    "Image": ["png", "jpg", "jpeg", "zip", "rar"],
    "Video": ["webm", "zip", "rar"]  # Clone Hero requires .webm for videos
}

def fetch_uploaded_highways(hw_type):
    """Fetch previously uploaded highways from the API."""
    try:
        content_type = "image_highways" if hw_type == "Image" else "video_highways"
        response = requests.get(f"{API_URL}/list_content/?content_type={content_type}", timeout=30)
        response.raise_for_status()
        return response.json().get("files", [])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {hw_type} highways: {e}")
        return []

def upload_highway(uploaded_file, hw_type):
    """Handle highway upload and provide UI feedback."""
    try:
        logger.info(f"Uploading {hw_type} highway: {uploaded_file.name}")
        files = {"file": uploaded_file}
        data = {"content_type": "image_highways" if hw_type == "Image" else "video_highways"}

        progress_bar = st.progress(0)
        with st.spinner("Uploading..."):
            response = requests.post(
                f"{API_URL}/upload_content/", files=files, data=data, timeout=60
            )
            progress_bar.progress(100)

        if response.status_code == 200:
            resp_json = response.json()
            if "error" in resp_json:
                st.error(f"Upload failed: {resp_json['error']}")
                logger.error(f"Server error: {resp_json['error']}")
            else:
                st.toast("✅ Highway uploaded successfully!", icon="🛣️")
                st.rerun()  # Refresh UI to show newly uploaded highways
        else:
            st.error(f"Upload failed: {response.text}")
            logger.error(f"Upload failed for {uploaded_file.name}, Status Code: {response.status_code}")
    except Exception as e:
        display_exception(e, f"Error uploading {hw_type} highway")

def delete_highway(hw_type, highway_name):
    """Delete a highway via API request."""
    try:
        content_type = "image_highways" if hw_type == "Image" else "video_highways"
        response = requests.delete(f"{API_URL}/delete_content/?content_type={content_type}&file={highway_name}", timeout=30)
        response.raise_for_status()
        st.toast(f"🗑️ Deleted {highway_name}", icon="🗑️")
        st.rerun()
    except requests.RequestException as e:
        logger.error(f"Failed to delete {highway_name}: {e}")
        st.error(f"Failed to delete {highway_name}")

def highways_page():
    """Streamlit UI for managing highways."""
    st.title("🛣️ Highway Manager")

    tab1, tab2 = st.tabs(["🖼️ Image Highways", "🎥 Video Highways"])

    for tab, hw_type in zip([tab1, tab2], ["Image", "Video"]):
        with tab:
            st.subheader(f"{hw_type} Highways")
            
            # Upload Section
            uploaded_file = st.file_uploader(
                f"Upload a {hw_type} highway", type=FILE_EXTENSIONS[hw_type]
            )
            if uploaded_file:
                upload_highway(uploaded_file, hw_type)

            # Display Existing Highways
            st.write(f"📂 **Existing {hw_type} Highways**")
            uploaded_highways = fetch_uploaded_highways(hw_type)

            if uploaded_highways:
                for highway in uploaded_highways:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"- `{highway}`")
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{highway}"):
                            delete_highway(hw_type, highway)
            else:
                st.info(f"No {hw_type.lower()} highways found.")