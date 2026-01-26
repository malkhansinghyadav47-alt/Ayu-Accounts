import streamlit as st
from db_helpers import add_group, get_all_groups

st.set_page_config(page_title="Account Groups", layout="wide")

st.title("🏷 Account Groups Management")

# -------------------------------
# Add New Group
# -------------------------------
st.subheader("➕ Add New Group")

with st.form("add_group_form"):
    group_name = st.text_input("Group Name", placeholder="e.g. Assets, Income, Expenses")
    submitted = st.form_submit_button("Save Group")

    if submitted:
        if not group_name.strip():
            st.warning("⚠️ Group name cannot be empty")
        else:
            try:
                add_group(group_name)
                st.success(f"✅ Group '{group_name}' added successfully")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# -------------------------------
# Show All Groups
# -------------------------------
st.subheader("📋 Existing Groups")

groups = get_all_groups()

if not groups:
    st.info("No groups found.")
else:
    table_data = []
    for g in groups:
        table_data.append({
            "ID": g["id"],
            "Group Name": g["group_name"]
        })

    st.dataframe(table_data, use_container_width=True)
