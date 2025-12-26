"""
Google OAuth integration for Streamlit authentication.

Uses streamlit-google-auth package for handling OAuth flow.
"""

import os
from typing import Optional

import streamlit as st


def is_google_oauth_enabled() -> bool:
    """Check if Google OAuth is enabled via environment variable."""
    return os.getenv("GOOGLE_OAUTH_ENABLED", "false").lower() == "true"


def get_google_oauth_config() -> dict:
    """Get Google OAuth configuration from environment."""
    return {
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8501"),
        "cookie_name": os.getenv("GOOGLE_OAUTH_COOKIE_NAME", "sdr_analytics_auth"),
        "cookie_key": os.getenv("GOOGLE_OAUTH_COOKIE_KEY", "default_key_change_me"),
    }


def init_google_auth():
    """
    Initialize Google OAuth authentication.

    Returns:
        Authenticate object or None if not configured
    """
    if not is_google_oauth_enabled():
        return None

    config = get_google_oauth_config()

    if not config["client_id"] or not config["client_secret"]:
        st.warning("⚠️ Google OAuth não configurado. Verifique as variáveis de ambiente.")
        return None

    try:
        from streamlit_google_auth import Authenticate

        return Authenticate(
            secret_credentials_path=None,  # Using env vars instead
            cookie_name=config["cookie_name"],
            cookie_key=config["cookie_key"],
            redirect_uri=config["redirect_uri"],
            client_id=config["client_id"],
            client_secret=config["client_secret"],
        )
    except Exception as e:
        st.error(f"Erro ao inicializar Google OAuth: {e}")
        return None


def handle_google_login() -> Optional[dict]:
    """
    Handle Google OAuth login flow.

    Returns:
        User info dict if authenticated, None otherwise
    """
    authenticator = init_google_auth()

    if authenticator is None:
        return None

    # Check if already authenticated via Google
    authenticator.check_authentification()

    if st.session_state.get("connected", False):
        return {
            "oauth_id": st.session_state.get("oauth_id"),
            "email": st.session_state.get("user_info", {}).get("email"),
            "name": st.session_state.get("user_info", {}).get("name"),
            "picture": st.session_state.get("user_info", {}).get("picture"),
        }

    return None


def render_google_login_button() -> bool:
    """
    Render Google login button.

    Returns:
        True if login button was clicked
    """
    authenticator = init_google_auth()

    if authenticator is None:
        return False

    authorization_url = authenticator.get_authorization_url()

    # Custom styled Google login button
    st.markdown(
        f"""
        <a href="{authorization_url}" target="_self" style="text-decoration: none;">
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                padding: 12px 24px;
                background: white;
                border: 1px solid #dadce0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            " onmouseover="this.style.boxShadow='0 2px 6px rgba(0,0,0,0.15)'"
               onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,0.08)'">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                     style="width: 20px; height: 20px;">
                <span style="color: #3c4043; font-size: 14px; font-weight: 500;">
                    Entrar com Google
                </span>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

    return False


def google_logout():
    """Clear Google OAuth session state."""
    keys_to_clear = ["connected", "oauth_id", "user_info", "google_user"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
