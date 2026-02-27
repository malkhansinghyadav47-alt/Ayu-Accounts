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
st.subheader("🖨 Print Options")

with st.expander("📁 Exporting & Printing", expanded=False):
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

    # -----------------------------
    # Print / Download Report
    # -----------------------------
    st.divider()
    st.subheader("🖨 Print or Download Report")

    if not df_all.empty:

        company_name = "Ayuquant Software Pvt Ltd"
        fy_label = f"{fy_start} to {fy_end}"

        # Optional styling (red negative values)
        styled_df = active_balance.copy()
        styled_df["Net Balance"] = styled_df["Net Balance"].apply(
            lambda x: f"<span style='color:red'>{x:,.2f}</span>" if x < 0 else f"{x:,.2f}"
        )

        html_table = styled_df.reset_index().to_html(index=False, escape=False)

        full_html = f"""
        <html>
        <head>
            <title>Account Balance Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                }}
                h2 {{
                    text-align: center;
                    margin-bottom: 5px;
                }}
                h4 {{
                    text-align: center;
                    margin-top: 0px;
                    color: gray;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 25px;
                }}
                th, td {{
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: right;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                td:first-child, th:first-child {{
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <h2>{company_name}</h2>
            <h4>Account Balance Report</h4>
            <h4>Financial Year: {fy_label}</h4>
            {html_table}
        </body>
        </html>
        """

        col1, col2 = st.columns(2)

        # 🖨 Print Button
        with col1:
            if st.button("🖨 Print"):
                st.components.v1.html(
                    full_html + "<script>window.print();</script>",
                    height=800,
                    scrolling=True
                )

        # 📥 Download HTML Button
        with col2:
            st.download_button(
                label="📥 Download HTML",
                data=full_html,
                file_name="account_balance_report.html",
                mime="text/html"
            )