import streamlit as st
from datetime import date

from db_helpers import (
    get_active_financial_year,
    get_all_accounts,
    add_transaction,
    get_transactions_by_year,
    indian_date
)

st.set_page_config(page_title="Transactions", layout="wide")

st.title("💳 Transaction Entry")

# ---------------------------------
# Active Financial Year
# ---------------------------------
active_year = get_active_financial_year()

if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

st.success(f"🟢 Active Financial Year : {active_year['label']}")

fy_id = active_year["id"] if "id" in active_year else None

st.divider()

# ---------------------------------
# Load Accounts
# ---------------------------------
accounts = get_all_accounts()

if not accounts:
    st.warning("No active accounts found.")
    st.stop()

acc_names = [a["name"] for a in accounts]
acc_map = {a["name"]: a["id"] for a in accounts}

# ---------------------------------
# Transaction Entry Form
# ---------------------------------
st.subheader("➕ New Transaction")

with st.form("transaction_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        txn_date = st.date_input("Transaction Date", value=date.today())

    with col2:
        from_account = st.selectbox("From Account (Credit)", acc_names)

    with col3:
        to_account = st.selectbox("To Account (Debit)", acc_names)

    col4, col5 = st.columns(2)

    with col4:
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")

    with col5:
        note = st.text_input("Narration / Note (optional)")

    submitted = st.form_submit_button("💾 Save Transaction")

    # -------------------------
    # Validations & Save
    # -------------------------
    if submitted:
        if from_account == to_account:
            st.error("❌ From and To account cannot be same.")
        elif amount <= 0:
            st.error("❌ Amount must be greater than zero.")
        else:
            try:
                from_id = acc_map[from_account]
                to_id = acc_map[to_account]

                add_transaction(
                    txn_date=str(txn_date),
                    from_acc_id=from_id,
                    to_acc_id=to_id,
                    amount=amount,
                    note=note,
                    financial_year_id=active_year["id"]
                )

                st.success("✅ Transaction saved successfully.")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# ---------------------------------
# Show Transactions List
# ---------------------------------
st.subheader(f"📋 Transactions for {active_year['label']}")

rows = get_transactions_by_year(active_year["id"])

if not rows:
    st.info("No transactions found for this year.")
else:
    table_data = []

    for r in rows:
        table_data.append({
            "Date": indian_date(r["txn_date"]),
            "From (Credit)": r["from_account"],
            "To (Debit)": r["to_account"],
            "Amount": f"{r['amount']:.2f}",
            "Note": r["note"] or ""
        })

    st.dataframe(table_data, use_container_width=True)
