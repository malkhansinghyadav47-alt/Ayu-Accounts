import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from io import BytesIO

from db_helpers import (
    get_active_financial_year,
    get_all_accounts,
    get_transactions_by_year,
)

st.set_page_config(page_title="Account Balances Report", layout="wide")

st.title("💳 Account Balances")

# -----------------------------
# Active Financial Year
# -----------------------------
active_year = get_active_financial_year()

if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

fy_id = active_year["id"]
fy_start = datetime.strptime(active_year["start_date"], "%Y-%m-%d").date()
fy_end = datetime.strptime(active_year["end_date"], "%Y-%m-%d").date()

st.caption(f"Financial Year: {active_year['label']} ({fy_start} to {fy_end})")

# -----------------------------
# Load Transactions
# -----------------------------
rows = get_transactions_by_year(fy_id)
df_all = pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

accounts = get_all_accounts()
active_accounts = [a for a in accounts if a["is_active"] == 1]
acc_names = sorted([a["name"] for a in active_accounts])

# -----------------------------
# Summary Section
# -----------------------------
st.divider()
st.subheader("📌 Summary")

if not df_all.empty:

    total_turnover = df_all["amount"].sum()

    total_cash_in = df_all[
        df_all["to_account"].str.contains("Cash", case=False, na=False)
    ]["amount"].sum()

    total_cash_out = df_all[
        df_all["from_account"].str.contains("Cash", case=False, na=False)
    ]["amount"].sum()

    net_cash = total_cash_in - total_cash_out

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Total Turnover", f"₹ {total_turnover:,.2f}")
    col2.metric("⬆ Cash In", f"₹ {total_cash_in:,.2f}")
    col3.metric("⬇ Cash Out", f"₹ {total_cash_out:,.2f}")

    st.metric("🏦 Net Cash Movement", f"₹ {net_cash:,.2f}")

else:
    st.info("No transactions found for this financial year.")

# -----------------------------
# Account Balance Section
# -----------------------------
st.divider()
st.subheader("📊 Account Balances")

if not df_all.empty:

    credits = (
        df_all.groupby("from_account")["amount"]
        .sum()
        .rename("Total_Out")
    )

    debits = (
        df_all.groupby("to_account")["amount"]
        .sum()
        .rename("Total_In")
    )

    balance_df = (
        pd.DataFrame(index=acc_names)
        .join(debits)
        .join(credits)
        .fillna(0)
    )

    balance_df["Net Balance"] = (
        balance_df["Total_In"] - balance_df["Total_Out"]
    )

    # Remove zero balance accounts
    active_balance = balance_df[
        (balance_df["Total_In"] != 0)
        | (balance_df["Total_Out"] != 0)
    ]

    if active_balance.empty:
        st.info("No account activity found.")
    else:
        styled_df = (
            active_balance.style
            .format("₹ {:,.2f}")
            .applymap(
                lambda x: "color:#ff4b4b;font-weight:bold"
                if x < 0
                else "color:#00c853;font-weight:bold",
                subset=["Net Balance"],
            )
        )

        st.dataframe(styled_df, use_container_width=True)

else:
    st.info("No transaction data available.")
    

# -----------------------------
# Export Options
# -----------------------------
st.divider()
st.subheader("🖨 Export / Print Options")

if not df_all.empty:

    # Excel Export
    excel_file = "account_balances.xlsx"
    active_balance.to_excel(excel_file)

    with open(excel_file, "rb") as f:
        st.download_button(
            label="📥 Download Excel",
            data=f,
            file_name=excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if not active_balance.empty:

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Accounts Balance Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [active_balance.reset_index().columns.tolist()] + \
           active_balance.reset_index().values.tolist()

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    elements.append(table)
    doc.build(elements)

    st.download_button(
        label="📄 Download PDF",
        data=pdf_buffer.getvalue(),
        file_name="accounts_balance_report.pdf",
        mime="application/pdf"
    )