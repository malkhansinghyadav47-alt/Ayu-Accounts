import streamlit as st
import shutil
import os
import time
from datetime import datetime

st.title("💾 Backup Management")

# Security Check
if st.session_state.get("role_name") != "Admin":
    st.error("Access Denied")
    st.stop()

DB_FILE = "business_ledger.db"

# --- SECTION 1: MANUAL BACKUP ---
with st.expander("💾 Backup Database"):
    st.subheader("Manual Backup")
    if st.button("Create Local Backup Copy"):
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy(DB_FILE, backup_name)
            st.success(f"✅ Backup created: {backup_name}")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # --- SECTION 2: DOWNLOAD ---
    st.subheader("Download Current Database")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            st.download_button(
                label="📥 Download .db File",
                data=f,
                file_name=f"business_ledger_{datetime.now().strftime('%Y%m%d')}.db",
                mime="application/octet-stream"
            )
    else:
        st.error("Database file not found!")

st.markdown("---")

# --- SECTION 3: RESTORE (HIDDEN IN EXPANDER) ---
# Initialize session state
if "restore_success" not in st.session_state:
    st.session_state.restore_success = False

# If restore just finished, show the success view outside the expander
if st.session_state.restore_success:
    st.success("✅ Database restored successfully!")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.restore_success = False
        st.rerun()
else:
    # Hide the "Open Mouth" inside an expander
    with st.expander("🛠️ Restore Database"):
        st.warning("⚠️ Warning: This will permanently overwrite the current database!")
        
        uploaded_file = st.file_uploader("Select .db file", type=["db"], key="restore_uploader")

        if uploaded_file:
            confirm = st.checkbox("I confirm that I want to overwrite the data.")
            
            if st.button("🔥 Execute Restore", disabled=not confirm):
                try:
                    with open(DB_FILE, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.session_state.restore_success = True
                    st.info("Restoring... Please wait.")
                    time.sleep(2) 
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error restoring database: {e}")