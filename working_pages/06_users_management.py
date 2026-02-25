import streamlit as st
from db_helpers import get_connection, hash_password

st.title("👥 User Management")

if "user_id" not in st.session_state:
    st.warning("Please login first")
    st.stop()

if st.session_state.role_name != "Admin":
    st.error("Access Denied")
    st.stop()

conn = get_connection()

# ===============================
# CREATE USER
# ===============================
with st.expander("➕ Create New User"):
    st.subheader("User Details")

    roles = conn.execute("SELECT * FROM roles").fetchall()
    role_dict = {r["role_name"]: r["id"] for r in roles}

    col1, col2 = st.columns(2)

    with col1:
        new_username = st.text_input("Username", key="create_username")
        new_fullname = st.text_input("Full Name", key="create_fullname")

    with col2:
        new_password = st.text_input("Password", type="password", key="create_password")
        selected_role = st.selectbox("Role", list(role_dict.keys()), key="create_role")

    if st.button("Create User", key="create_user_btn"):

        if not new_username or not new_password:
            st.error("Username and Password required")
        else:
            hashed_pw = hash_password(new_password)

            try:
                conn.execute("""
                    INSERT INTO users (username, full_name, password_hash, role_id, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (new_username, new_fullname, hashed_pw, role_dict[selected_role]))

                conn.commit()
                st.success("User created successfully")
                st.rerun()

            except:
                st.error("Username already exists")

# ===============================
# USER LIST
# ===============================

st.divider()
with st.expander("📋 Existing Users"):

    users = conn.execute("""
        SELECT u.id, u.username, u.full_name, u.is_active, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        ORDER BY u.id DESC
    """).fetchall()

    for user in users:

        with st.expander(f"{user['username']} ({user['role_name']})"):

            col1, col2 = st.columns(2)

            with col1:
                edit_username = st.text_input(
                    "Username",
                    value=user["username"],
                    key=f"edit_username_{user['id']}"
                )

                edit_fullname = st.text_input(
                    "Full Name",
                    value=user["full_name"] or "",
                    key=f"edit_fullname_{user['id']}"
                )

                edit_role = st.selectbox(
                    "Role",
                    list(role_dict.keys()),
                    index=list(role_dict.keys()).index(user["role_name"]),
                    key=f"edit_role_{user['id']}"
                )

            with col2:
                edit_active = st.checkbox(
                    "Active",
                    value=bool(user["is_active"]),
                    key=f"edit_active_{user['id']}"
                )

            col_save, col_delete = st.columns(2)

            # UPDATE USER
            if col_save.button("💾 Save", key=f"save_{user['id']}"):

                # Check duplicate username (excluding current user)
                existing = conn.execute("""
                    SELECT id FROM users WHERE username = ? AND id != ?
                """, (edit_username, user["id"])).fetchone()

                if existing:
                    st.error("Username already exists")
                else:
                    conn.execute("""
                        UPDATE users
                        SET username = ?, full_name = ?, role_id = ?, is_active = ?
                        WHERE id = ?
                    """, (
                        edit_username,
                        edit_fullname,
                        role_dict[edit_role],
                        int(edit_active),
                        user["id"]
                    ))
                    conn.commit()
                    st.success("User updated")
                    st.rerun()

            # DELETE USER
            if user["id"] == st.session_state.user_id:
                col_delete.warning("You cannot delete yourself")
            else:
                if col_delete.button("🗑 Delete", key=f"delete_{user['id']}"):
                    conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
                    conn.commit()
                    st.warning("User deleted")
                    st.rerun()