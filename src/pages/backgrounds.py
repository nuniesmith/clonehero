import streamlit as st
from loguru import logger
import requests
from src.utils import display_exception, API_URL


def backgrounds_page():
    """
    UI for uploading backgrounds (images/videos).
    Supports separate sub-type selection (Image or Video) with file validation.
    """
    st.title("🎨 Manage Backgrounds")
    
    bg_type = st.radio("Select Background Type", ["Image", "Video"], horizontal=True)

    file_extensions = {
        "Image": ["png", "jpg", "jpeg", "zip", "rar"],
        "Video": ["webm", "mp4", "avi", "mpeg", "zip", "rar"]
    }

    uploaded_file = st.file_uploader(
        f"Upload a {bg_type} background", type=file_extensions[bg_type]
    )

    if uploaded_file:
        try:
            logger.info(f"Uploading {bg_type} background: {uploaded_file.name}")
            files = {"file": uploaded_file}
            data = {"content_type": "image_backgrounds" if bg_type == "Image" else "video_backgrounds"}

            with st.spinner("Uploading..."):
                response = requests.post(
                    f"{API_URL}/upload_content/", files=files, data=data, timeout=30
                )

            if response.status_code == 200:
                resp_json = response.json()
                if "error" in resp_json:
                    st.error(f"Upload failed: {resp_json['error']}")
                    logger.error(f"Server error: {resp_json['error']}")
                else:
                    st.success(resp_json.get("message", "Background uploaded successfully!"))
                    st.write("**Stored Files:**")
                    for f in resp_json.get("files", []):
                        st.write(f"- {f}")
            else:
                st.error(f"Upload failed: {response.text}")
                logger.error(f"Upload failed for {uploaded_file.name}, Status Code: {response.status_code}")

        except Exception as e:
            display_exception(e, f"Error uploading {bg_type} background")