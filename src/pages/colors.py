import streamlit as st
from loguru import logger
import requests
from src.utils import display_exception, API_URL


def colors_page():
    """UI for uploading color profiles (.ini or archives)."""
    st.title("🎨 Manage Colors")

    uploaded_file = st.file_uploader(
        "Upload a color profile (.ini) or an archive (.zip/.rar) with multiple .ini files",
        type=["ini", "zip", "rar"]
    )

    if uploaded_file:
        try:
            logger.info(f"Uploading color profile: {uploaded_file.name}")
            files = {"file": uploaded_file}
            data = {"content_type": "colors"}

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
                    st.success(resp_json.get("message", "Color profile uploaded successfully!"))
                    st.write("**Stored Files:**")
                    for f in resp_json.get("files", []):
                        st.write(f"- {f}")
            else:
                st.error(f"Upload failed: {response.text}")
                logger.error(f"Upload failed for {uploaded_file.name}, Status Code: {response.status_code}")

        except Exception as e:
            display_exception(e, "Error uploading color profile")