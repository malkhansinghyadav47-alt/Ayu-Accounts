import streamlit as st
import pandas as pd
from datetime import datetime, date

from db_helpers import (
    get_active_financial_year,
    get_all_accounts,
    add_transaction,
    get_transactions_by_year,
    get_transaction_summary,
    delete_transaction,
    update_transaction,
    indian_date
)

st.set_page_config(page_title="Transactions", layout="wide")

# Initialize a version counter for the editor key if it doesn't exist
if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

st.title("💳 Transaction Management")

# ---------------------------------
# 1. Active Financial Year Validation
# ---------------------------------
active_year = get_active_financial_year()
if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

fy_id = active_year["id"]
fy_start = datetime.strptime(active_year['start_date'], "%Y-%m-%d").date()
fy_end = datetime.strptime(active_year['end_date'], "%Y-%m-%d").date()

# --- Summary Section ---
total_amt, txn_count = get_transaction_summary(fy_id)
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Total Turnover", f"₹ {total_amt:,.2f}")
col_m2.metric("Total Entries", txn_count)
col_m3.metric("Financial Year", active_year['label'])

st.divider()

# ---------------------------------
# 2. Load Accounts
# ---------------------------------
accounts = get_all_accounts()
active_accounts = [a for a in accounts if a["is_active"] == 1]
acc_names = sorted([a["name"] for a in active_accounts])
acc_map = {a["name"]: a["id"] for a in active_accounts}

# ---------------------------------
# 3. Transaction Entry Form
# ---------------------------------
with st.expander("➕ Add New Transaction", expanded=False):
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            default_date = date.today()
            if default_date < fy_start: default_date = fy_start
            if default_date > fy_end: default_date = fy_end
            txn_date = c1.date_input("Transaction Date", value=default_date)
        from_acc = c2.selectbox("From (Credit)", acc_names, index=None)
        to_acc = c3.selectbox("To (Debit)", acc_names, index=None)

        c4, c5 = st.columns([1, 2])
        amt = c4.number_input("Amount", min_value=0.0, format="%.2f")
        memo = c5.text_input("Note")

        if st.form_submit_button("💾 Save Transaction", use_container_width=True):
            if from_acc and to_acc and amt > 0:
                add_transaction(str(txn_date), acc_map[from_acc], acc_map[to_acc], amt, memo, fy_id, 1)
                st.success("✅ Saved!")
                st.rerun()
            else:
                st.error("❌ Please check your inputs.")

st.divider()

# ... (Keep imports and active_year validation the same)

# ---------------------------------
# 4. Interactive Transaction List
# ---------------------------------
st.subheader("📋 Transaction History")
rows = get_transactions_by_year(fy_id)

if not rows:
    st.info("No transactions found.")
else:
    df = pd.DataFrame([dict(r) for r in rows])

    # Search Bar
    search_q = st.text_input("🔍 Search history...", placeholder="Filter by account or note").lower()
    if search_q:
        mask = (df['from_account'].str.lower().str.contains(search_q) | 
                df['to_account'].str.lower().str.contains(search_q) | 
                df['note'].str.lower().str.contains(search_q, na=False))
        filtered_df = df[mask].reset_index(drop=True)
    else:
        filtered_df = df.reset_index(drop=True)

    editor_key = f"txn_editor_{st.session_state.editor_version}"

    # --- UPDATED DATA EDITOR ---
    edited_df = st.data_editor(
        filtered_df,
        column_order=("txn_date", "from_account", "to_account", "amount", "note"),
        column_config={
            "txn_date": st.column_config.TextColumn("Date", disabled=True),
            # ENABLED ACCOUNT CHANGES VIA SELECTBOX
            "from_account": st.column_config.SelectboxColumn(
                "From (Credit)", 
                options=acc_names, 
                required=True
            ),
            "to_account": st.column_config.SelectboxColumn(
                "To (Debit)", 
                options=acc_names, 
                required=True
            ),
            "amount": st.column_config.NumberColumn("Amount", format="₹ %.2f", min_value=1),
            "note": st.column_config.TextColumn("Note"),
        },
        use_container_width=True,
        num_rows="dynamic",
        key=editor_key
    )

    # ---------------------------------
    # 5. Safe Save / Cancel Logic
    # ---------------------------------
    state = st.session_state[editor_key]
    if state.get("deleted_rows") or state.get("edited_rows"):
        st.warning("⚠️ You have unsaved changes.")
        col_s1, col_s2, _ = st.columns([1, 1, 4])

        if col_s1.button("✅ Confirm Save", type="primary", use_container_width=True):
            try:
                # Process Deletions
                for row_idx in state["deleted_rows"]:
                    delete_transaction(int(filtered_df.iloc[row_idx]["id"]))
                
                # Process Edits
                for idx_str, changes in state["edited_rows"].items():
                    row_idx = int(idx_str)
                    txn_id = int(filtered_df.iloc[row_idx]["id"])
                    
                    # Get existing values
                    old_from_name = filtered_df.iloc[row_idx]["from_account"]
                    old_to_name = filtered_df.iloc[row_idx]["to_account"]
                    old_amount = filtered_df.iloc[row_idx]["amount"]
                    old_note = filtered_df.iloc[row_idx]["note"]

                    # Apply changes or keep old values
                    new_from_name = changes.get("from_account", old_from_name)
                    new_to_name = changes.get("to_account", old_to_name)
                    new_amt = changes.get("amount", old_amount)
                    new_note = changes.get("note", old_note)

                    # Validate that accounts aren't the same
                    if new_from_name == new_to_name:
                        st.error(f"❌ Error in row {row_idx+1}: From and To accounts cannot be the same.")
                        st.stop()

                    # Convert names back to IDs using the acc_map
                    from_id = acc_map[new_from_name]
                    to_id = acc_map[new_to_name]

                    # Updated helper call
                    update_transaction(txn_id, new_amt, new_note, from_id, to_id)
                
                st.success("Changes saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving: {e}")

        if col_s2.button("❌ Cancel & Undo", use_container_width=True):
            st.session_state.editor_version += 1
            st.rerun()