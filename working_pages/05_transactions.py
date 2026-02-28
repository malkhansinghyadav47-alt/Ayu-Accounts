import streamlit as st
import pandas as pd
from datetime import datetime, date

from db_helpers import (
    get_active_financial_year,
    get_all_accounts,
    add_transaction,
    get_transactions_by_year,
    delete_transaction,
    update_transaction
)

st.set_page_config(page_title="Transactions", layout="wide")

# -----------------------------
# Session State
# -----------------------------
if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

if "form_reset_key" not in st.session_state:
    st.session_state.form_reset_key = 0

st.title("💳 Transaction Management")

# -----------------------------
# 1. Active Financial Year
# -----------------------------
active_year = get_active_financial_year()
if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

fy_id = active_year["id"]
fy_start = datetime.strptime(active_year["start_date"], "%Y-%m-%d").date()
fy_end = datetime.strptime(active_year["end_date"], "%Y-%m-%d").date()

# -----------------------------
# Load Data
# -----------------------------
rows = get_transactions_by_year(fy_id)
df_all = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

accounts = get_all_accounts()
active_accounts = [a for a in accounts if a["is_active"] == 1]
acc_names = sorted([a["name"] for a in active_accounts])
acc_map = {a["name"]: a["id"] for a in active_accounts}

# -----------------------------
# 2. Summary
# -----------------------------
if not df_all.empty:
    total_out = df_all[df_all['from_account'].str.contains('Cash', case=False, na=False)]['amount'].sum()
    total_in = df_all[df_all['to_account'].str.contains('Cash', case=False, na=False)]['amount'].sum()
    turnover = df_all["amount"].sum()
else:
    total_out = total_in = turnover = 0

c1, c2, c3 = st.columns(3)
c1.metric("Total Inflow (+)", f"₹ {total_in:,.2f}")
c2.metric("Total Outflow (-)", f"₹ {total_out:,.2f}")
c3.metric("Total Turnover", f"₹ {turnover:,.2f}")

st.divider()

# -----------------------------
# 3. Add Transaction (FIXED)
# -----------------------------
with st.expander("➕ Add New Transaction", expanded=False):
    with st.form(f"transaction_form_{st.session_state.form_reset_key}"):

        c1, c2, c3 = st.columns(3)

        with c1:
            auto_date = min(max(date.today(), fy_start), fy_end)
            txn_date = st.date_input("Date", value=auto_date)

        from_acc = c2.selectbox("From (Credit / Out) 🔴", acc_names, index=None)
        to_acc = c3.selectbox("To (Debit / In) 🟢", acc_names, index=None)

        c4, c5 = st.columns([1, 2])
        amt = c4.number_input("Amount", min_value=0.00, format="%.2f")
        memo = c5.text_input("Note")

        submitted = st.form_submit_button("💾 Save Transaction", use_container_width=True)

        if submitted:
            errors = []

            if not from_acc or not to_acc:
                errors.append("From and To accounts are required.")
            elif from_acc == to_acc:
                errors.append("From and To accounts cannot be same.")

            if not (fy_start <= txn_date <= fy_end):
                errors.append("Date must be within active financial year.")

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                try:
                    add_transaction(
                        str(txn_date),
                        acc_map[from_acc],
                        acc_map[to_acc],
                        amt,
                        memo,
                        fy_id,
                        1
                    )
                    st.success("✅ Transaction saved successfully")

                    # Reset form ONLY on success
                    st.session_state.form_reset_key += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to save: {e}")

st.divider()

# -----------------------------
# 4. Transaction History
# -----------------------------
with st.expander("📋 View/Edit Transactions", expanded=False):
    st.subheader("📋 Transaction History")

    if not df_all.empty:
        df_all["Edit_Amt"] = df_all["amount"]

        search_q = st.text_input("🔍 Search history...").lower()
        df_view = df_all.copy()

        if search_q:
            mask = (
                df_view["from_account"].str.lower().str.contains(search_q) |
                df_view["to_account"].str.lower().str.contains(search_q) |
                df_view["note"].fillna("").str.lower().str.contains(search_q)
            )
            df_view = df_view[mask]

        editor_key = f"txn_editor_{st.session_state.editor_version}"

        edited_df = st.data_editor(
            df_view,
            column_order=("txn_date", "from_account", "to_account", "Edit_Amt", "note"),
            column_config={
                "txn_date": st.column_config.TextColumn("Date", disabled=True),
                "from_account": st.column_config.SelectboxColumn("From", options=acc_names),
                "to_account": st.column_config.SelectboxColumn("To", options=acc_names),
                "Edit_Amt": st.column_config.NumberColumn("Amount (₹)", format="%.2f"),
                "note": st.column_config.TextColumn("Note", width="large"),
            },
            disabled=["txn_date"],
            use_container_width=True,
            key=editor_key
        )

        state = st.session_state[editor_key]

        if state.get("deleted_rows") or state.get("edited_rows"):
            st.warning("⚠️ Unsaved changes")

            c1, c2, _ = st.columns([1, 1, 4])

            if c1.button("✅ Confirm Save", type="primary"):
                try:
                    for idx in state.get("deleted_rows", []):
                        delete_transaction(int(df_view.iloc[idx]["id"]))

                    for idx_str, changes in state.get("edited_rows", {}).items():
                        row_idx = int(idx_str)
                        row = df_view.iloc[row_idx]

                        update_transaction(
                            int(row["id"]),
                            changes.get("Edit_Amt", row["amount"]),
                            changes.get("note", row["note"]),
                            acc_map[changes.get("from_account", row["from_account"])],
                            acc_map[changes.get("to_account", row["to_account"])]
                        )

                    st.success("✅ Changes saved")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

            if c2.button("❌ Undo"):
                st.session_state.editor_version += 1
                st.rerun()

# -----------------------------
# 5. Account Balances
# -----------------------------
st.divider()
with st.expander("📊 View Account Balances", expanded=False):
    st.subheader("📊 Account Balances")

    if not df_all.empty:
        credits = df_all.groupby('from_account')['amount'].sum().rename('Total_Out')
        debits = df_all.groupby('to_account')['amount'].sum().rename('Total_In')

        balance_df = (
            pd.DataFrame(index=acc_names)
            .join(debits)
            .join(credits)
            .fillna(0)
        )

        balance_df['Net Balance'] = balance_df['Total_In'] - balance_df['Total_Out']

        active_balance = balance_df[
            (balance_df['Total_In'] > 0) | (balance_df['Total_Out'] > 0)
        ]

        st.table(
            active_balance.style
            .format("₹ {:,.2f}")
            .applymap(
                lambda x: "color:#ff4b4b;font-weight:bold" if x < 0 else "color:#00c853;font-weight:bold",
                subset=['Net Balance']
            )
        )
