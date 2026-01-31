import streamlit as st
from db_helpers import (
    get_all_groups,
    add_account,
    get_all_accounts,
    update_account,
    toggle_account_status,
    delete_account,
    can_delete_account    
)

st.set_page_config(page_title="Accounts Master", layout="wide")

# --- HELPER AT TOP ---
def clear_form_key(key):
    if key in st.session_state:
        st.session_state[key] = False

st.title("👤 Accounts Master")

# -------------------------------
# Add New Account
# -------------------------------
# Using an expander here keeps the focus on the list, but easy to add new
with st.expander("➕ Add New Account", expanded=False):
    if "acc_form_version" not in st.session_state:
        st.session_state.acc_form_version = 0

    groups = get_all_groups()
    if not groups:
        st.warning("⚠️ Please create Groups first.")
    else:
        group_labels = [g["group_name"] for g in groups]
        group_map = {g["group_name"]: g["id"] for g in groups}
        group_reverse_map = {g["id"]: g["group_name"] for g in groups}

        form_key = f"add_acc_v_{st.session_state.acc_form_version}"

        with st.form(form_key):
            col1, col2 = st.columns(2)
            with col1:
                acc_name = st.text_input("Account Name *")
                phone = st.text_input("Phone (optional)")
            with col2:
                selected_group = st.selectbox("Select Group *", group_labels, index=None, placeholder="Choose a group...")
                address = st.text_input("Address (optional)")

            if st.form_submit_button("💾 Save Account", use_container_width=True):
                if not acc_name.strip() or not selected_group:
                    st.error("⚠️ Name and Group are required.")
                else:
                    try:
                        add_account(acc_name.strip(), group_map[selected_group], phone.strip(), address.strip())
                        st.session_state.acc_form_version += 1
                        st.toast(f"✅ {acc_name} added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

st.divider()

# -------------------------------
# Existing Accounts
# -------------------------------
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.subheader("📋 Existing Accounts")
with col_h2:
    search_q = st.text_input("🔍 Search", placeholder="Name or Group...").lower()

accounts = get_all_accounts()

if not accounts:
    st.info("No accounts found.")
else:
    # Filtering logic
    filtered_accounts = [
        a for a in accounts 
        if search_q in a['name'].lower() or search_q in a['group_name'].lower()
    ]

    for a in filtered_accounts:
        # Checkbox key for the update protection
        upd_check_key = f"conf_upd_acc_{a['id']}"
        
        # Row-based display
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1.5])
            
            c1.markdown(f"**{a['name']}**")
            c2.write(f"🏷️ {a['group_name']}")
            
            if a["is_active"] == 1:
                c3.success("Active")
            else:
                c3.error("Inactive")

            # Management Popover
            with c4.popover("⚙️ Edit", use_container_width=True):
                # Edit Fields
                edit_name = st.text_input("Account Name", value=a["name"], key=f"en_{a['id']}")
                edit_group = st.selectbox("Group", group_labels, index=group_labels.index(a["group_name"]), key=f"eg_{a['id']}")
                edit_phone = st.text_input("Phone", value=a["phone"] or "", key=f"ep_{a['id']}")
                edit_addr = st.text_input("Address", value=a.get("address", "") or "", key=f"ea_{a['id']}")
                
                # Safety Checkbox for Update
                confirm_upd = st.checkbox("Confirm changes", key=upd_check_key)
                
                # Action Buttons (Update & Toggle)
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("💾 Update", key=f"ub_{a['id']}", disabled=not confirm_upd, on_click=clear_form_key, args=(upd_check_key,)):
                        update_account(a["id"], edit_name, group_map[edit_group], edit_phone, edit_addr)
                        st.rerun()
                
                with btn_col2:
                    status_btn_label = "Deactivate" if a["is_active"] == 1 else "Activate"
                    if st.button(status_btn_label, key=f"tb_{a['id']}"):
                        toggle_account_status(a["id"], 0 if a["is_active"] == 1 else 1)
                        st.rerun()

                # --- SAFE DELETE SECTION (Inside Popover) ---
                st.divider()
                
                # Check if account is used
                is_unused = can_delete_account(a["id"]) 
                
                if is_unused:
                    st.write("🗑️ **Delete Account**")
                    del_check_key = f"conf_del_acc_{a['id']}"
                    confirm_del = st.checkbox("Confirm permanent deletion", key=del_check_key)
                    
                    if st.button(
                        "❌ Delete Permanently", 
                        key=f"del_btn_{a['id']}", 
                        disabled=not confirm_del, 
                        type="primary",
                        on_click=clear_form_key,
                        args=(del_check_key,),
                        use_container_width=True
                    ):
                        delete_account(a["id"])
                        st.toast("🗑️ Account deleted")
                        st.rerun()
                else:
                    st.info("🔒 Linked to data. Use 'Deactivate' instead.")