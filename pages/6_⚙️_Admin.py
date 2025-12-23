"""
Admin Panel - User Management

Superadmin-only page for managing users, viewing audit logs,
and system administration.
"""

from dotenv import load_dotenv

load_dotenv()


import streamlit as st

from src.auth.auth_manager import AuthManager
from src.auth.database import SessionLocal
from src.auth.models import AuditLog, User

# Require superadmin access
AuthManager.require_superadmin()

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

# Render user sidebar
from src.dashboard_utils import render_user_sidebar

render_user_sidebar()

st.title("⚙️ Admin Panel - User Management")
st.markdown("**Superadmin Only** - Manage users and view system logs")
st.markdown("---")

# Tabs for different admin functions
tab1, tab2, tab3 = st.tabs(["👥 Users", "📋 Audit Logs", "➕ Create User"])

# ================================================================
# TAB 1: USER MANAGEMENT
# ================================================================
with tab1:
    st.header("👥 User Management")

    db = SessionLocal()
    try:
        # Fetch all users
        users = db.query(User).order_by(User.created_at.desc()).all()

        if not users:
            st.info("No users found in the system.")
        else:
            st.metric("Total Users", len(users))
            st.markdown("---")

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                filter_role = st.selectbox("Filter by Role", ["All", "superadmin", "user"], key="filter_role")
            with col2:
                filter_status = st.selectbox(
                    "Filter by Status",
                    ["All", "Active", "Inactive"],
                    key="filter_status",
                )

            # Apply filters
            filtered_users = users
            if filter_role != "All":
                filtered_users = [u for u in filtered_users if u.role == filter_role]
            if filter_status == "Active":
                filtered_users = [u for u in filtered_users if u.is_active]
            elif filter_status == "Inactive":
                filtered_users = [u for u in filtered_users if not u.is_active]

            st.markdown(f"**Showing {len(filtered_users)} of {len(users)} users**")
            st.markdown("---")

            # Display users in cards
            for user in filtered_users:
                status_icon = "🟢 Active" if user.is_active else "🔴 Inactive"
                with st.expander(f"**{user.username}** ({user.role}) - {status_icon}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**User Details:**")
                        st.write(f"- **ID**: {user.id}")
                        st.write(f"- **Username**: {user.username}")
                        st.write(f"- **Email**: {user.email}")
                        st.write(f"- **Role**: {user.role}")
                        st.write(f"- **Status**: {'Active' if user.is_active else 'Inactive'}")

                    with col2:
                        st.write("**Activity:**")
                        st.write(f"- **Created**: {user.created_at.strftime('%d/%m/%Y %H:%M')}")
                        if user.last_login:
                            st.write(f"- **Last Login**: {user.last_login.strftime('%d/%m/%Y %H:%M')}")
                        else:
                            st.write("- **Last Login**: Never")
                        if user.created_by:
                            creator = db.query(User).filter(User.id == user.created_by).first()
                            if creator:
                                st.write(f"- **Created By**: {creator.username}")

                    # Action buttons
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if user.is_active:
                            if st.button("🔒 Deactivate", key=f"deactivate_{user.id}"):
                                user.is_active = False
                                db.commit()
                                st.success(f"User {user.username} deactivated!")
                                st.rerun()
                        else:
                            if st.button("🔓 Activate", key=f"activate_{user.id}"):
                                user.is_active = True
                                db.commit()
                                st.success(f"User {user.username} activated!")
                                st.rerun()

                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{user.id}"):
                            st.session_state.edit_user_id = user.id
                            st.info("Edit functionality coming soon!")

                    with col3:
                        # Don't allow deleting own account or last superadmin
                        can_delete = user.id != st.session_state.user_id
                        if user.role == "superadmin":
                            superadmin_count = sum(1 for u in users if u.role == "superadmin" and u.is_active)
                            can_delete = can_delete and superadmin_count > 1

                        if can_delete:
                            if st.button("🗑️ Delete", key=f"delete_{user.id}", type="secondary"):
                                if st.session_state.get(f"confirm_delete_{user.id}"):
                                    db.delete(user)
                                    db.commit()
                                    st.success(f"User {user.username} deleted!")
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{user.id}"] = True
                                    st.warning("Click again to confirm deletion")
                        else:
                            st.caption("Cannot delete this user")

    finally:
        db.close()

# ================================================================
# TAB 2: AUDIT LOGS
# ================================================================
with tab2:
    st.header("📋 Audit Logs")

    db = SessionLocal()
    try:
        # Fetch recent logs (last 100)
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

        if not logs:
            st.info("No audit logs found.")
        else:
            st.metric("Recent Actions", len(logs))
            st.caption("Showing last 100 actions")
            st.markdown("---")

            # Filters
            col1, col2 = st.columns(2)
            with col1:
                unique_actions = sorted(list(set(log.action for log in logs)))
                filter_action = st.selectbox("Filter by Action", ["All"] + unique_actions)
            with col2:
                user_ids = [log.user_id for log in logs]
                unique_users = sorted(list(set(db.query(User.username).filter(User.id.in_(user_ids)).all())))
                filter_user = st.selectbox("Filter by User", ["All"] + [u[0] for u in unique_users])

            # Apply filters
            filtered_logs = logs
            if filter_action != "All":
                filtered_logs = [log for log in filtered_logs if log.action == filter_action]
            if filter_user != "All":
                user_obj = db.query(User).filter(User.username == filter_user).first()
                if user_obj:
                    filtered_logs = [log for log in filtered_logs if log.user_id == user_obj.id]

            st.markdown(f"**Showing {len(filtered_logs)} of {len(logs)} logs**")
            st.markdown("---")

            # Display logs in table
            for log in filtered_logs:
                user = db.query(User).filter(User.id == log.user_id).first()
                username = user.username if user else f"User#{log.user_id}"

                col1, col2, col3, col4 = st.columns([2, 2, 3, 3])
                with col1:
                    st.write(f"**{log.timestamp.strftime('%d/%m %H:%M')}**")
                with col2:
                    st.write(f"👤 {username}")
                with col3:
                    st.write(f"🔹 {log.action}")
                with col4:
                    if log.resource:
                        st.write(f"📄 {log.resource}")
                    else:
                        st.write("-")

                st.markdown("---")

    finally:
        db.close()

# ================================================================
# TAB 3: CREATE USER
# ================================================================
with tab3:
    st.header("➕ Create New User")

    with st.form("create_user_form"):
        st.write("**User Information**")

        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input(
                "Username *",
                placeholder="e.g., john.doe",
                help="Unique username for login",
            )
            new_email = st.text_input(
                "Email *",
                placeholder="e.g., john@empresa.com",
                help="User's email address",
            )

        with col2:
            new_password = st.text_input(
                "Password *",
                type="password",
                placeholder="Min 8 characters",
                help="Initial password (user should change on first login)",
            )
            new_password_confirm = st.text_input(
                "Confirm Password *", type="password", placeholder="Type password again"
            )

        new_role = st.selectbox(
            "Role *",
            ["user", "superadmin"],
            help="user = Dashboard access | superadmin = Full system access",
        )

        st.markdown("---")
        submit = st.form_submit_button("✅ Create User", type="primary", use_container_width=True)

        if submit:
            # Validation
            errors = []

            if not new_username or not new_email or not new_password:
                errors.append("All fields marked with * are required")

            if new_password != new_password_confirm:
                errors.append("Passwords do not match")

            if len(new_password) < 8:
                errors.append("Password must be at least 8 characters")

            # Check if username/email already exists
            db = SessionLocal()
            try:
                existing_user = (
                    db.query(User).filter((User.username == new_username) | (User.email == new_email)).first()
                )

                if existing_user:
                    if existing_user.username == new_username:
                        errors.append(f"Username '{new_username}' already exists")
                    if existing_user.email == new_email:
                        errors.append(f"Email '{new_email}' already exists")

                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Create user
                    new_user = User(
                        username=new_username,
                        email=new_email,
                        role=new_role,
                        is_active=True,
                        created_by=st.session_state.user_id,
                    )
                    new_user.set_password(new_password)

                    db.add(new_user)
                    db.commit()

                    # Log action
                    from src.auth.auth_manager import log_action

                    log_action(
                        st.session_state.user_id,
                        "create_user",
                        new_username,
                        {"role": new_role},
                    )

                    st.success(f"✅ User '{new_username}' created successfully!")
                    st.info(f"📧 Credentials: {new_username} / {new_password}")
                    st.warning("⚠️ User should change password on first login")

                    # Clear form
                    st.rerun()

            finally:
                db.close()

# Footer
st.markdown("---")
st.caption("Admin Panel v1.0 - Superadmin access only")
