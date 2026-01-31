import streamlit as st
from datetime import date

from db_helpers import (
    get_active_financial_year,
    get_all_financial_years,
    set_active_financial_year,
    add_financial_year,
    update_financial_year,
    delete_financial_year,
    can_delete_financial_year,
    indian_date
)

st.set_page_config(page_title="Financial Year Setup", layout="wide")
st.title("📅 Financial Year Management")

# ===============================
# CURRENT ACTIVE YEAR
# ===============================
active_year = get_active_financial_year()

st.subheader("🔁 Current Active Financial Year")
if active_year:
    st.success(
        f"Active Year: {active_year['label']} "
        f"({indian_date(active_year['start_date'])} to {indian_date(active_year['end_date'])})"
    )
else:
    st.warning("⚠️ No active financial year selected")

st.divider()

# ===============================
# ADD FINANCIAL YEAR
# ===============================
st.subheader("➕ Add Financial Year")

with st.form("add_fy"):
    label = st.text_input(
        "Financial Year",
        placeholder="e.g. 2049-50"
    )

    submitted = st.form_submit_button("Add Financial Year")

    if submitted:
        success, msg = add_financial_year(label)

        if success:
            st.success("✅ Financial Year added successfully")
            st.rerun()
        else:
            st.warning(f"⚠️ {msg}")


st.divider()

# ===============================
# ALL FINANCIAL YEARS
# ===============================
st.subheader("📋 All Financial Years")

# Define callback once outside the loop
def clear_checkbox(key):
    if key in st.session_state:
        st.session_state[key] = False

years = get_all_financial_years()
if not years:
    st.info("No financial years found")
else:
    for y in years:
        with st.container(border=True):
            # We add a 5th column for the 'Manage' tools
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

            col1.write(f"**{y['label']}**")
            col2.write(f"📅 {indian_date(y['start_date'])}")
            col3.write(f"🏁 {indian_date(y['end_date'])}")

            # Active Status Logic
            if y["is_active"] == 1:
                col4.success("✅ ACTIVE")
            else:
                if col4.button("Set Active", key=f"active_{y['id']}", use_container_width=True):
                    set_active_financial_year(y["id"])
                    st.rerun()

            # --- INTEGRATED EDIT/DELETE TOOLS ---
            with col5.popover("⚙️ Manage", use_container_width=True):
                st.markdown(f"**Manage {y['label']}**")
                
                # Update Section
                new_label = st.text_input(
                    "Edit Label",
                    y["label"],
                    key=f"lbl_{y['id']}"
                )
                upd_check_key = f"conf_upd_{y['id']}"
                confirm_update = st.checkbox("Confirm label change", key=upd_check_key)

                if st.button(
                    "Update Label", 
                    key=f"upd_{y['id']}", 
                    disabled=not confirm_update,
                    on_click=clear_checkbox,
                    args=(upd_check_key,),
                    use_container_width=True
                ):
                    try:
                        update_financial_year(y["id"], new_label)
                        st.success("Updated!")
                        st.rerun()
                    except ValueError as e:
                        st.warning(str(e))

                st.divider()

                # Delete Section
                if can_delete_financial_year(y["id"]):
                    st.write("⚠️ **Danger Zone**")
                    del_check_key = f"conf_del_{y['id']}"
                    confirm_delete = st.checkbox("Confirm deletion", key=del_check_key)
                    
                    if st.button(
                        "❌ Delete Year", 
                        key=f"del_{y['id']}", 
                        disabled=not confirm_delete, 
                        type="primary",
                        on_click=clear_checkbox,
                        args=(del_check_key,),
                        use_container_width=True
                    ):
                        delete_financial_year(y["id"])
                        st.rerun()
                else:
                    st.info("🔒 Cannot delete: Year has linked data.")