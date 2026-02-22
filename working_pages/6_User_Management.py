import streamlit as st
from db_helpers import get_connection, hash_password

st.title("👥 User Management")

if "user_id" not in st.session_state:
    st.warning("Please login first")
    st.stop()

if st.session_state.role_name != "Admin":
    st.error("Access Denied")
    st.stop()
    
st.subheader("➕ Create New User")

conn = get_connection()

roles = conn.execute("SELECT * FROM roles").fetchall()
role_dict = {r["role_name"]: r["id"] for r in roles}

col1, col2 = st.columns(2)

with col1:
    new_username = st.text_input("Username")
    new_fullname = st.text_input("Full Name")

with col2:
    new_password = st.text_input("Password", type="password")
    selected_role = st.selectbox("Role", list(role_dict.keys()))

if st.button("Create User"):

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
            
st.subheader("➕ Create New User")

conn = get_connection()

roles = conn.execute("SELECT * FROM roles").fetchall()
role_dict = {r["role_name"]: r["id"] for r in roles}

col1, col2 = st.columns(2)

with col1:
    new_username = st.text_input("Username")
    new_fullname = st.text_input("Full Name")

with col2:
    new_password = st.text_input("Password", type="password")
    selected_role = st.selectbox("Role", list(role_dict.keys()))

if st.button("Create User"):

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
            
    