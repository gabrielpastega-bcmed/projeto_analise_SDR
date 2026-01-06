"""
Login Page - Authentication Entry Point

Users must login here before accessing the dashboard.
"""

from dotenv import load_dotenv

load_dotenv()  # Load environment variables before importing auth modules

import streamlit as st

from src.auth.auth_manager import AuthManager

# Page configuration
st.set_page_config(
    page_title="Login - SDR Analytics",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for better login page aesthetics
st.markdown(
    """
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Title
st.markdown('<h1 class="main-title">🔐 SDR Analytics</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Sistema de Análise de Atendimento</p>', unsafe_allow_html=True
)

# Check if already logged in
if AuthManager.is_authenticated():
    user_info = AuthManager.get_current_user()

    st.success(f"✅ Você já está autenticado como **{user_info['username']}**")

    # Show user info
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Usuário", user_info["username"])
    with col2:
        role_display = "🔑 Super Admin" if user_info["is_superadmin"] else "👤 Usuário"
        st.metric("Perfil", role_display)

    st.info("👈 Use o menu lateral para navegar entre as páginas do dashboard.")

    st.markdown("---")

    # Logout button
    if st.button("🚪 Fazer Logout", width="stretch"):
        AuthManager.logout()
        # Also clear Google OAuth session
        from src.auth.google_auth import google_logout

        google_logout()
        st.rerun()

else:
    # Check for Google OAuth callback
    from src.auth.google_auth import (
        handle_google_login,
        is_google_oauth_enabled,
        render_google_login_button,
    )

    # Handle Google OAuth callback if returning from Google
    if is_google_oauth_enabled():
        google_user = handle_google_login()
        if google_user:
            st.session_state.google_user = google_user
            user_name = google_user.get("name", google_user.get("email"))
            st.success(
                f"✅ Login com Google bem-sucedido! Bem-vindo(a), **{user_name}**!"
            )
            st.balloons()
            import time

            time.sleep(1)
            st.rerun()

    # Login form header
    st.markdown("### 🔓 Acesse sua conta")

    # Google OAuth button (if enabled)
    if is_google_oauth_enabled():
        st.markdown("---")
        st.markdown("**Acesso rápido:**")
        render_google_login_button()
        st.markdown("")
        st.markdown("---")
        st.markdown("**Ou use suas credenciais:**")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "👤 Usuário",
            placeholder="Digite seu usuário",
            help="Nome de usuário fornecido pelo administrador",
        )

        password = st.text_input(
            "🔑 Senha",
            type="password",
            placeholder="Digite sua senha",
            help="Senha confidencial - não compartilhe com ninguém",
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            submit = st.form_submit_button("🔓 Entrar", width="stretch")
        with col2:
            remember = st.checkbox("Lembrar", help="Manter sessão ativa")

        if submit:
            if not username or not password:
                st.error("❌ Por favor, preencha usuário e senha.")
            else:
                with st.spinner("🔄 Autenticando..."):
                    user = AuthManager.login(username, password)

                    if user:
                        # Store user info in session
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.session_state.email = user.email
                        st.session_state.role = user.role
                        st.session_state.is_superadmin = user.is_superadmin()

                        st.success(
                            f"✅ Login bem-sucedido! Bem-vindo(a), **{user.username}**!"
                        )
                        st.balloons()

                        # Add a small delay to show success message
                        import time

                        time.sleep(1)

                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos. Tente novamente.")
                        st.warning(
                            "⚠️ Se esqueceu sua senha, entre em contato com um administrador."
                        )

    # Help section
    st.markdown("---")
    with st.expander("❓ Precisa de ajuda?"):
        st.markdown(
            """
        **Primeiro acesso:**
        - Entre em contato com um administrador para criar sua conta
        - Você receberá suas credenciais por email
        - Troque sua senha após o primeiro login

        **Problemas de acesso:**
        - Verifique se está usando o usuário e senha corretos
        - Certifique-se de que sua conta está ativa
        - Contate o suporte técnico se o problema persistir

        **Suporte:**
        - Email: suporte@empresa.com.br
        - Administradores do sistema podem resetar senhas
        """
        )

    # Footer
    st.markdown("---")
    st.caption("🔒 Acesso seguro e protegido • SDR Analytics Dashboard v0.9.0")
