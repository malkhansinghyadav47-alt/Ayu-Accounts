import streamlit as st
from db_helpers import (
    get_active_financial_year,
    get_all_accounts_simple,
    add_opening_balance,
    get_opening_balances,
    get_opening_balance
)

st.set_page_config(page_title="Opening Balances", layout="wide")

st.title("💰 Opening Balance Entry")

# -------------------------------
# Active Financial Year
# -------------------------------
active_year = get_active_financial_year()

if not active_year:
    st.error("❌ No Active Financial Year set. Please activate a year first.")
    st.stop()

fy_id = active_year["id"]
fy_label = active_year["label"]

st.success(f"🟢 Active Financial Year : {fy_label}")
st.divider()

# -------------------------------
# Account Selection
# -------------------------------
accounts = get_all_accounts_simple()

if not accounts:
    st.warning("⚠️ No accounts found. Please create accounts first.")
    st.stop()

acc_labels = [a["name"] for a in accounts]
acc_map = {a["name"]: a["id"] for a in accounts}

selected_acc = st.selectbox("Select Account *", acc_labels)
acc_id = acc_map[selected_acc]

# -------------------------------
# Existing Opening Balance
# -------------------------------
existing_amount = get_opening_balance(acc_id, fy_id)

if existing_amount != 0:
    st.info(
        f"📌 Existing Opening Balance: "
        f"{abs(existing_amount):,.2f} "
        f"({'Debit' if existing_amount > 0 else 'Credit'})"
    )

# -------------------------------
# Entry / Update Form
# -------------------------------
with st.form("opening_balance_form"):
    col1, col2 = st.columns(2)

    with col1:
        initial_value = float(abs(existing_amount)) if existing_amount is not None else 0.0

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=initial_value,
            step=0.01,
            format="%.2f"
        )

    with col2:
        dc_type = st.selectbox(
            "Type",
            ["Debit", "Credit"],
            index=0 if existing_amount >= 0 else 1
        )

    submitted = st.form_submit_button("Save / Update Opening Balance")

    if submitted:
        try:
            if amount == 0:
                # Zero means reset to zero (safe overwrite)
                add_opening_balance(acc_id, fy_id, 0)
                st.success("✅ Opening balance reset to zero")
            else:
                final_amount = amount if dc_type == "Debit" else -amount
                add_opening_balance(acc_id, fy_id, final_amount)
                st.success(f"✅ Opening balance saved for '{selected_acc}'")

            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")

st.divider()

# -------------------------------
# Show Opening Balances
# -------------------------------
st.subheader("📋 Opening Balances for " + fy_label)

balances = get_opening_balances(fy_id)

if not balances:
    st.info("No opening balances entered yet.")
else:
    table_data = []
    for b in balances:
        amt = b["amount"]
        table_data.append({
            "Account": b["name"],
            "Debit": f"{amt:,.2f}" if amt > 0 else "",
            "Credit": f"{abs(amt):,.2f}" if amt < 0 else ""
        })

    st.dataframe(table_data, use_container_width=True)
