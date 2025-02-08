import streamlit as st
from src.pages.song_generator import song_generation_page
from src.pages.songs import songs_page
from src.pages.database_explorer import database_explorer_page
from src.pages.colors import colors_page
from src.pages.backgrounds import backgrounds_page
from src.pages.highways import highways_page

def format_status(status):
    """Formats the status message for better clarity and debugging."""
    status_mapping = {
        "🟢 Online": "✅ Service is Running",
        "🔴 Offline": "❌ Service is Down (Check Logs)",
        "🔴 Connection Error": "⚠️ Cannot Reach Service (Network Issue)",
        "🔴 Timeout": "⏳ Service Timeout (Possible Firewall Issue)",
        "🔴 404 Not Found": "🚫 Missing Endpoint (`/health` may not exist)",
        "🔴 Server Error": "🔥 Backend Error (Check API Logs)"
    }
    return status_mapping.get(status, status)

def setup_sidebar(service_statuses):
    """Define sidebar UI elements using native Streamlit components."""
    st.sidebar.image("assets/ch_icon.png", width=50)
    st.sidebar.title("Clone Hero Manager")
    
    # Navigation Menu (Pages First)
    st.sidebar.markdown("### 📂 Navigation")
    PAGES = {
        "📁 Database Explorer": database_explorer_page,
        "📤 Upload Songs": songs_page,
        "🎵 Generate Songs": song_generation_page,
        "🎨 Colors": colors_page,
        "🌆 Backgrounds": backgrounds_page,
        "🛣️ Highways": highways_page,
    }
    
    menu_selection = st.sidebar.radio("📌 Select a Page", list(PAGES.keys()))
    
    # Divider for separation
    st.sidebar.markdown("---")

    # Service Health Status (Below Navigation)
    st.sidebar.markdown("### 🖥️ Service Status")
    
    for service, status in service_statuses.items():
        formatted_status = format_status(status)
        st.sidebar.write(f"- **{service}**: {formatted_status}")

        if "Connection Error" in status:
            st.sidebar.warning("🚨 Connection Issue Detected! 🚨")
            st.sidebar.info(f"Try: `docker exec -it clonehero_frontend curl -I {service.lower()}`")
        
        if "Timeout" in status:
            st.sidebar.warning("⏳ Service took too long to respond. Possible firewall/network issue.")
        
        if "404 Not Found" in status:
            st.sidebar.warning("🚫 The `/health` endpoint is missing!")
            st.sidebar.info(f"Run: `curl -I {service.lower()}/status` to verify.")
        
        if "Offline" in status:
            st.sidebar.warning("🔍 Check if the service URL is correct and accessible.")
            st.sidebar.info(f"Verify with: `curl -I {service.lower()}`")

    # Refresh & Cache Clearing Options
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh App"):
        st.rerun()

    if st.sidebar.button("♻️ Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Footer Info
    st.sidebar.markdown("---")
    st.sidebar.write("🛠️ **Clone Hero Manager** - v1.0.0")
    st.sidebar.write("🚀 Developed with ❤️ using Streamlit")

    return PAGES[menu_selection]