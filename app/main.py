"""Main entry point for the AI Multimodal Interview Agent."""

import logging
import sys
import os
from importlib.metadata import version, PackageNotFoundError

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_app_version() -> str:
    """Read app version from package metadata or fallback to VERSION file."""
    try:
        return version("ai-interview-agent")
    except PackageNotFoundError:
        pass
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip()
    return "1.0.0"


APP_VERSION = _get_app_version()


def setup_page_config():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="AI Interview Agent",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "current_page": "home",
        "interview_started": False,
        "interview_controller": None,
        "candidate_name": "",
        "candidate_email": "",
        "candidate_id": "",
        "interview_id": "",
        "session_id": "",
        "questions": [],
        "interview_results": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def sidebar_navigation():
    """Render sidebar navigation."""
    with st.sidebar:
        st.title("🎯 AI Interview Agent")
        st.markdown("---")

        st.markdown("### Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state["current_page"] = "home"
            st.rerun()

        if st.session_state.get("interview_started"):
            if st.button("📝 Interview", use_container_width=True):
                st.session_state["current_page"] = "interview"
                st.rerun()

        if st.session_state.get("interview_results"):
            if st.button("📊 Results", use_container_width=True):
                st.session_state["current_page"] = "results"
                st.rerun()
            if st.button("🔄 Replay", use_container_width=True):
                st.session_state["current_page"] = "replay"
                st.rerun()

        st.markdown("---")
        st.markdown("### Status")
        status = "🟢 Active" if st.session_state.get("interview_started") else "⚪ Idle"
        st.markdown(f"Interview: {status}")

        candidate = st.session_state.get("candidate_name", "None")
        st.markdown(f"Candidate: {candidate}")

        st.markdown("---")
        st.caption(f"Powered by AI | v{APP_VERSION}")


def main():
    """Main application entry point."""
    setup_page_config()
    init_session_state()

    # Ensure output directories — side effects only here, never on config import
    from app.config import ensure_directories
    ensure_directories()

    sidebar_navigation()

    page = st.session_state.get("current_page", "home")

    try:
        if page == "home":
            from frontend.pages.home import show
            show()
        elif page == "interview":
            from frontend.pages.interview import show
            show()
        elif page == "results":
            from frontend.pages.results import show
            show()
        elif page == "replay":
            from frontend.pages.replay import show
            show()
        else:
            st.error(f"Unknown page: {page}")
            from frontend.pages.home import show
            show()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.exception("Page rendering error")
        if st.button("🔄 Reset"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
