import streamlit as st
import requests
from loguru import logger
from src.utils import API_URL, display_exception

def highways_page():
    """
    UI for uploading highways (images/videos), similar to backgrounds but
    supporting 'image_highways' and 'video_highways' content types.
    """
    st.title("🛣️ Manage Highways")
    
    hw_type = st.radio("Select Highway Type", ["Image", "Video"], horizontal=True)
    
    file_extensions = {
        "Image": ["png", "jpg", "jpeg", "zip", "rar"],
        "Video": ["webm", "zip", "rar"]  # Clone Hero requires .webm for videos
    }

    uploaded_file = st.file_uploader(
        f"Upload a {hw_type} highway", type=file_extensions[hw_type]
    )

    if uploaded_file:
        try:
            logger.info(f"Uploading {hw_type} highway: {uploaded_file.name}")
            files = {"file": uploaded_file}
            data = {"content_type": "image_highways" if hw_type == "Image" else "video_highways"}

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
                    st.success(resp_json.get("message", "Highway uploaded successfully!"))
                    st.write("**Stored Files:**")
                    for f in resp_json.get("files", []):
                        st.write(f"- {f}")
            else:
                st.error(f"Upload failed: {response.text}")
                logger.error(f"Upload failed for {uploaded_file.name}, Status Code: {response.status_code}")

        except Exception as e:
            display_exception(e, f"Error uploading {hw_type} highway")