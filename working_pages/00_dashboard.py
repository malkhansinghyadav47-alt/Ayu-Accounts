import streamlit as st

from db_helpers import (
    get_active_financial_year,
    get_total_income,
    get_total_expense,
    get_cash_balance,
    get_receivable,
    get_payable,
    get_monthly_income_expense
)

st.set_page_config(page_title="Financial Dashboard", layout="wide")

st.title("🏠 Financial Dashboard")

# ------------------ FETCH DATA ------------------

total_income = get_total_income()
total_expense = get_total_expense()
net_profit = total_income - total_expense
cash_balance = get_cash_balance()
receivable = get_receivable()
payable = get_payable()
monthly_df = get_monthly_income_expense()

# ------------------ KPI CARDS ------------------

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("💰 Total Income", f"₹ {total_income:,.2f}")
col2.metric("💸 Total Expense", f"₹ {total_expense:,.2f}")
col3.metric("📈 Net Profit", f"₹ {net_profit:,.2f}")
col4.metric("🏦 Cash Balance", f"₹ {cash_balance:,.2f}")
col5.metric("🧾 Receivable", f"₹ {receivable:,.2f}")
col6.metric("💳 Payable", f"₹ {payable:,.2f}")

st.divider()

# ------------------ CHART ------------------

st.subheader("📈 Monthly Income vs Expense")

if not monthly_df.empty:
    st.line_chart(monthly_df.set_index("month")[["income", "expense"]])
else:
    st.info("No monthly data available.")

st.divider()

# ------------------ ALERTS ------------------

st.subheader("⚠ Alerts")

if net_profit < 0:
    st.error("Business is in LOSS")

if payable > cash_balance:
    st.warning("Payables exceed Cash Balance")

if receivable > payable:
    st.success("Receivables look healthy")