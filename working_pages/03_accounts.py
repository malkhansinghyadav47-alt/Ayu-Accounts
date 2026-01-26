import streamlit as st
from db_helpers import get_all_groups, add_account, get_all_accounts

st.set_page_config(page_title="Accounts Master", layout="wide")

st.title("👤 Accounts Master")

# -------------------------------
# Add New Account
# -------------------------------
st.subheader("➕ Add New Account")

groups = get_all_groups()

if not groups:
    st.warning("⚠️ Please create Groups first before adding Accounts.")
    st.stop()

group_labels = [g["group_name"] for g in groups]
group_map = {g["group_name"]: g["id"] for g in groups}

with st.form("add_account_form"):
    col1, col2 = st.columns(2)

    with col1:
        acc_name = st.text_input("Account Name *")
        phone = st.text_input("Phone (optional)")

    with col2:
        selected_group = st.selectbox("Select Group *", group_labels)
        address = st.text_input("Address (optional)")

    submitted = st.form_submit_button("Save Account")

    if submitted:
        if not acc_name.strip():
            st.warning("⚠️ Account name is required")
        else:
            try:
                group_id = group_map[selected_group]
                add_account(acc_name, group_id, phone, address)
                st.success(f"✅ Account '{acc_name}' added successfully")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# -------------------------------
# Show All Accounts
# -------------------------------
st.subheader("📋 Existing Accounts")

accounts = get_all_accounts()

if not accounts:
    st.info("No accounts found.")
else:
    table_data = []
    for a in accounts:
        table_data.append({
            "ID": a["id"],
            "Account Name": a["name"],
            "Group": a["group_name"],
            "Phone": a["phone"],
            "Status": "Active" if a["is_active"] == 1 else "Inactive"
        })

    st.dataframe(table_data, use_container_width=True)
