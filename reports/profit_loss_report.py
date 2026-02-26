import streamlit as st
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime

try:
    import openpyxl
    excel_available = True
except ImportError:
    excel_available = False


from db_helpers import (
    get_active_financial_year,
    get_connection
)

st.set_page_config(page_title="Profit & Loss Report", layout="wide")

st.title("📈 Profit & Loss Report")

# -----------------------------
# 1. Active Financial Year
# -----------------------------
active_year = get_active_financial_year()
if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

financial_year_id = active_year["id"]
fy_start = datetime.strptime(active_year["start_date"], "%Y-%m-%d").date()
fy_end = datetime.strptime(active_year["end_date"], "%Y-%m-%d").date()

st.success(f"🟢 Active FY: {active_year['label']}")

# -----------------------------
# 2. Date Filter
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("From Date", value=fy_start, min_value=fy_start, max_value=fy_end)

with col2:
    end_date = st.date_input("To Date", value=fy_end, min_value=fy_start, max_value=fy_end)

if start_date > end_date:
    st.warning("⚠️ Start date cannot be after end date.")
    st.stop()

# -----------------------------
# 3. Fetch Income & Expense Data
# -----------------------------
def get_profit_loss(financial_year_id, start_date, end_date):
    """
    Logic:
    - Income increases when money is credited to Income accounts (from_ac_id)
    - Expense increases when money is debited to Expense accounts (to_ac_id)
    """

    with get_connection() as conn:
        cur = conn.cursor()

        # -----------------------------
        # INCOME (Group ID = 3)
        # -----------------------------
        cur.execute("""
            SELECT a.name AS account_name,
                   SUM(t.amount) AS total_income
            FROM transactions t
            JOIN accounts a ON a.id = t.from_acc_id
            WHERE a.group_id = 3
              AND t.financial_year_id = ?
              AND t.txn_date BETWEEN ? AND ?
            GROUP BY a.id, a.name
            ORDER BY total_income DESC
        """, (financial_year_id, start_date, end_date))

        income_rows = cur.fetchall()

        # -----------------------------
        # EXPENSE (Group ID = 4)
        # -----------------------------
        cur.execute("""
            SELECT a.name AS account_name,
                   SUM(t.amount) AS total_expense
            FROM transactions t
            JOIN accounts a ON a.id = t.to_acc_id
            WHERE a.group_id = 4
              AND t.financial_year_id = ?
              AND t.txn_date BETWEEN ? AND ?
            GROUP BY a.id, a.name
            ORDER BY total_expense DESC
        """, (financial_year_id, start_date, end_date))

        expense_rows = cur.fetchall()

    return income_rows, expense_rows


income_rows, expense_rows = get_profit_loss(
    financial_year_id,
    start_date.strftime("%Y-%m-%d"),
    end_date.strftime("%Y-%m-%d")
)

income_data = [{"Income Account": r["account_name"], "Amount": round(r["total_income"], 2)} for r in income_rows]
expense_data = [{"Expense Account": r["account_name"], "Amount": round(r["total_expense"], 2)} for r in expense_rows]

df_income = pd.DataFrame(income_data)
df_expense = pd.DataFrame(expense_data)

total_income = df_income["Amount"].sum() if not df_income.empty else 0.0
total_expense = df_expense["Amount"].sum() if not df_expense.empty else 0.0

net_profit = total_income - total_expense

# -----------------------------
# 4. Display Income & Expense Tables
# -----------------------------
st.divider()
st.subheader("💰 Income Section")

if df_income.empty:
    st.warning("No income transactions found.")
else:
    st.dataframe(df_income, use_container_width=True)

st.subheader("💸 Expense Section")

if df_expense.empty:
    st.warning("No expense transactions found.")
else:
    st.dataframe(df_expense, use_container_width=True)

# -----------------------------
# 5. Summary
# -----------------------------
st.divider()
st.subheader("📊 Profit & Loss Summary")

c1, c2, c3 = st.columns(3)

c1.metric("Total Income", f"₹ {total_income:,.2f}")
c2.metric("Total Expense", f"₹ {total_expense:,.2f}")

if net_profit >= 0:
    c3.success(f"✅ Net Profit: ₹ {net_profit:,.2f}")
else:
    c3.error(f"❌ Net Loss: ₹ {abs(net_profit):,.2f}")

# -----------------------------
# 6. Export Options
# -----------------------------
st.divider()
st.subheader("📥 Export Options")

with st.expander("📁 Exporting & Printing", expanded=False):
    colA, colB, colC = st.columns(3)

    # Combined Data for Export
    export_df = pd.DataFrame({
        "Type": (["Income"] * len(df_income)) + (["Expense"] * len(df_expense)),
        "Account Name": (
            df_income["Income Account"].tolist() if not df_income.empty else []
        ) + (
            df_expense["Expense Account"].tolist() if not df_expense.empty else []
        ),
        "Amount": (
            df_income["Amount"].tolist() if not df_income.empty else []
        ) + (
            df_expense["Amount"].tolist() if not df_expense.empty else []
        )
    })

    # CSV Download
    csv_data = export_df.to_csv(index=False).encode("utf-8")

    colA.download_button(
        "⬇️ Download CSV",
        data=csv_data,
        file_name=f"profit_loss_{active_year['label']}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # Excel Download (only if openpyxl installed)
    with colB:
        st.markdown("### 📗 Excel Export")

        if export_df.empty:
            st.warning("⚠️ No data available to export.")
        else:
            try:
                import pandas as pd
                import openpyxl
                from io import BytesIO

                output = BytesIO()

                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    export_df.to_excel(writer, sheet_name="Profit & Loss", index=False)

                output.seek(0)

                st.download_button(
                    "⬇️ Download Excel",
                    data=output,
                    file_name=f"profit_loss_{active_year['label']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except ImportError:
                st.warning("⚠️ Excel export not available (openpyxl missing).")
                st.info("Run: py -m pip install openpyxl")

            except Exception as e:
                st.error(f"❌ Excel export failed: {e}")

    # -----------------------------
    # 7. Print Option (HTML Download)
    # -----------------------------
    with colC:
        st.markdown("### 🖨 Print Profit & Loss")

        print_html = f"""
        <html>
        <head>
            <title>Profit & Loss Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                h2 {{
                    text-align: center;
                }}
                h4 {{
                    text-align: center;
                    color: gray;
                    margin-top: 0px;
                }}
                .summary {{
                    margin-bottom: 15px;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    font-size: 14px;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background: #f2f2f2;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-top: 25px;
                }}
                @media print {{
                    body {{
                        padding: 0;
                    }}
                    .summary {{
                        border: none;
                    }}
                }}
            </style>
        </head>
        <body>

            <h2>📈 Profit & Loss Report</h2>
            <h4>Financial Year: {active_year['label']}</h4>

            <div class="summary">
                <b>From:</b> {start_date.strftime('%d-%m-%Y')} &nbsp;&nbsp;
                <b>To:</b> {end_date.strftime('%d-%m-%Y')}<br><br>

                <b>Total Income:</b> ₹ {total_income:,.2f}<br>
                <b>Total Expense:</b> ₹ {total_expense:,.2f}<br><br>

                <b>Net Result:</b> {"Net Profit" if net_profit >= 0 else "Net Loss"} : ₹ {abs(net_profit):,.2f}
            </div>

            <div class="section-title">💰 Income</div>
            {df_income.to_html(index=False) if not df_income.empty else "<p>No income found.</p>"}

            <div class="section-title">💸 Expenses</div>
            {df_expense.to_html(index=False) if not df_expense.empty else "<p>No expenses found.</p>"}

        </body>
        </html>
        """

        st.download_button(
            "🖨 Download Print P&L (HTML)",
            data=print_html.encode("utf-8"),
            file_name=f"ProfitLoss_{active_year['label']}_{start_date}_{end_date}.html",
            mime="text/html",
            use_container_width=True
        )

        st.info("✅ Download HTML → Open in Browser → Press CTRL+P to Print")
