import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt

from db_helpers import (
    get_active_financial_year,
    get_cash_bank_accounts,
    get_opening_balance,
    get_cash_flow_summary,
    get_cash_flow_transactions,
    get_cash_closing_balance
)

st.title("💵 Cash Flow Report")
st.markdown("### Cash / Bank Receipts & Payments Summary")

active_year = get_active_financial_year()

if not active_year:
    st.warning("⚠️ No Active Financial Year Found.")
    st.stop()

financial_year_id = active_year["id"]

# ----------------------------------------
# Fetch Cash/Bank Accounts
# ----------------------------------------
cash_accounts = get_cash_bank_accounts(financial_year_id)

if not cash_accounts:
    st.error("❌ No Cash/Bank Accounts found. Please check CASH_BANK_GROUP_IDS in db_helpers.py")
    st.stop()

acc_dict = {f"{row[1]} (ID:{row[0]})": row[0] for row in cash_accounts}

# ----------------------------------------
# UI Filters
# ----------------------------------------
col1, col2, col3 = st.columns([3, 2, 2])

with col1:
    selected_acc = st.selectbox("🏦 Select Cash / Bank Account", list(acc_dict.keys()))
    account_id = acc_dict[selected_acc]
    account_name = selected_acc.split("(ID:")[0].strip()

with col2:
    start_date = st.date_input("📅 Start Date", value=datetime.strptime(active_year["start_date"], "%Y-%m-%d"))

with col3:
    end_date = st.date_input("📅 End Date", value=datetime.strptime(active_year["end_date"], "%Y-%m-%d"))

start_date = start_date.strftime("%Y-%m-%d")
end_date = end_date.strftime("%Y-%m-%d")

# ----------------------------------------
# Get Summary
# ----------------------------------------
opening_balance = get_opening_balance(account_id, financial_year_id)
summary = get_cash_flow_summary(account_id, financial_year_id, start_date, end_date)
closing_balance = get_cash_closing_balance(account_id, financial_year_id, start_date, end_date)

cash_in = summary["cash_in"]
cash_out = summary["cash_out"]
net_flow = summary["net_cash_flow"]

# ----------------------------------------
# Display Summary Cards
# ----------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.info(f"📌 Opening Balance\n\n₹ {opening_balance:,.2f}")
c2.success(f"⬆️ Cash Inflow\n\n₹ {cash_in:,.2f}")
c3.error(f"⬇️ Cash Outflow\n\n₹ {cash_out:,.2f}")

if net_flow >= 0:
    c4.success(f"✅ Net Cash Flow\n\n₹ {net_flow:,.2f}")
else:
    c4.error(f"❌ Net Cash Flow\n\n₹ {abs(net_flow):,.2f}")

st.markdown("---")

st.markdown(f"## 🏁 Closing Balance: ₹ {closing_balance:,.2f}")

# ----------------------------------------
# Transactions Table
# ----------------------------------------
rows = get_cash_flow_transactions(account_id, financial_year_id, start_date, end_date)

data = []
running_balance = opening_balance

for r in rows:
    txn_id = r[0]
    txn_date = r[1]
    narration = r[2]
    from_acc = r[3]
    to_acc = r[4]
    from_id = r[5]
    to_id = r[6]
    amount = r[7]

    inflow = 0
    outflow = 0

    if to_id == account_id:
        inflow = amount
        running_balance += amount

    elif from_id == account_id:
        outflow = amount
        running_balance -= amount

    data.append({
        "Date": txn_date,
        "Narration": narration,
        "From": from_acc,
        "To": to_acc,
        "Inflow": inflow,
        "Outflow": outflow,
        "Balance": running_balance
    })


df = pd.DataFrame(data)

st.markdown("### 📌 Cash / Bank Transactions")
st.dataframe(df, use_container_width=True)

# ----------------------------------------
# Monthly Summary
# ----------------------------------------
st.markdown("---")
st.markdown("## 📅 Monthly Cash Flow Summary")

if df.empty:
    st.warning("⚠️ No data available for monthly summary.")
else:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Month"] = df["Date"].dt.strftime("%b-%Y")

    monthly_summary = df.groupby("Month").agg({
        "Inflow": "sum",
        "Outflow": "sum"
    }).reset_index()

    monthly_summary["Net Flow"] = monthly_summary["Inflow"] - monthly_summary["Outflow"]

    # Sorting month properly
    monthly_summary["MonthSort"] = pd.to_datetime(monthly_summary["Month"], format="%b-%Y")
    monthly_summary = monthly_summary.sort_values("MonthSort")
    monthly_summary = monthly_summary.drop(columns=["MonthSort"])

    st.dataframe(monthly_summary, use_container_width=True)

    # ----------------------------------------
    # Monthly Chart
    # ----------------------------------------
    st.markdown("### 📊 Monthly Inflow / Outflow Chart")

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(monthly_summary["Month"], monthly_summary["Inflow"], marker="o", label="Inflow")
    ax.plot(monthly_summary["Month"], monthly_summary["Outflow"], marker="o", label="Outflow")
    ax.plot(monthly_summary["Month"], monthly_summary["Net Flow"], marker="o", label="Net Flow")

    ax.set_xlabel("Month")
    ax.set_ylabel("Amount (₹)")
    ax.set_title("Monthly Cash Flow Trend")
    ax.legend()
    ax.grid(True)

    plt.xticks(rotation=45)

    st.pyplot(fig)


# ----------------------------------------
# Export Options
# ----------------------------------------
st.markdown("---")
colA, colB, colC = st.columns(3)

# ---------- CSV ----------
with colA:
    st.markdown("### 📄 CSV Export")
    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download CSV",
        data=csv_data,
        file_name=f"cash_flow_{account_name}_{active_year['label']}.csv",
        mime="text/csv",
        use_container_width=True
    )
# ---------- Excel ----------
# ---------- Excel ----------
with colB:
    st.markdown("### 📗 Excel Export")

    try:
        def to_excel_v2(df_in):
            # This import MUST happen inside the function to avoid NameErrors
            import io
            import pandas as pd
            
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                df_in.to_excel(writer, sheet_name="Cash Flow", index=False)
            
            return output_buffer.getvalue()

        if not df.empty:
            # We process the data immediately
            processed_data = to_excel_v2(df)
            
            st.download_button(
                label="⬇️ Download Excel",
                data=processed_data,
                file_name=f"cash_flow_{account_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("⚠️ No data to export")

    except Exception as e:
        # This will show us the module search path if it fails again
        import sys
        st.error(f"❌ Error: {e}")
        st.write(f"System Path: {sys.modules.get('io')}")

# ---------- Print HTML ----------
with colC:
    st.markdown("### 🖨 Print / PDF")

    if not df.empty:
        print_html = f"""
        <html>
        <head>
            <title>Cash Flow Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                h2 {{
                    text-align: center;
                }}
                .summary {{
                    margin-bottom: 15px;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    font-size: 13px;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 6px;
                    text-align: left;
                }}
                th {{
                    background: #f2f2f2;
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
            <h2>Cash Flow Report</h2>

            <div class="summary">
                <b>Account:</b> {account_name}<br>
                <b>Financial Year:</b> {active_year['label']}<br>
                <b>From:</b> {start_date} &nbsp;&nbsp; <b>To:</b> {end_date}<br><br>

                <b>Opening Balance:</b> ₹ {opening_balance:,.2f}<br>
                <b>Total Inflow:</b> ₹ {cash_in:,.2f}<br>
                <b>Total Outflow:</b> ₹ {cash_out:,.2f}<br>
                <b>Net Cash Flow:</b> ₹ {net_flow:,.2f}<br>
                <b>Closing Balance:</b> ₹ {closing_balance:,.2f}<br>
            </div>

            {df.to_html(index=False)}
        </body>
        </html>
        """

        st.download_button(
            "🖨 Download Print Report (HTML)",
            data=print_html.encode("utf-8"),
            file_name=f"cash_flow_{account_name}_{start_date}_{end_date}.html",
            mime="text/html",
            use_container_width=True
        )

        st.info("✅ Download HTML → Open in browser → CTRL+P → Save as PDF / Print")

    else:
        st.button("🖨 Download Print Report (HTML)", use_container_width=True, disabled=True)
