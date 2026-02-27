import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

from db_helpers import (
    get_active_financial_year,
    get_day_book_transactions,
    get_day_book_summary
)

st.title("📒 Day Book")
with st.expander("### Change the date", expanded=False):
    active_year = get_active_financial_year()

    if not active_year:
        st.warning("⚠️ No Active Financial Year Found.")
        st.stop()

    financial_year_id = active_year["id"]

    # ----------------------------------------
    # Filters
    # ----------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "📅 Start Date",
            value=datetime.strptime(active_year["start_date"], "%Y-%m-%d")
        )

    with col2:
        end_date = st.date_input(
            "📅 End Date",
            value=datetime.strptime(active_year["end_date"], "%Y-%m-%d")
        )

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")
    
# ----------------------------------------
# Summary
# ----------------------------------------
summary = get_day_book_summary(financial_year_id, start_date, end_date)

st.markdown("---")
st.caption(f"From {start_date} to {end_date} (Financial Year: {active_year['label']} )")

# Combine both into one info box to save vertical space on mobile
amt = summary['total_amount']
color_code = "#28a745" if amt >= 0 else "#dc3545"  # Professional Green/Red

st.markdown(
    f"""
    <div style="
        background-color: rgba(33, 37, 41, 0.05); 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid {color_code};
        display: flex; 
        justify-content: space-between; 
        align-items: center;">
        <div>
            <div style="font-size: 0.8rem; color: gray;">Day Book</div>
            <div style="font-size: 1.1rem; font-weight: bold;">{summary['total_entries']} Entries</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.8rem; color: gray;">Total Balance</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: {color_code};">
                ₹ {amt:,.2f}
            </div>
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)

st.markdown("---")

# ----------------------------------------
# Fetch Transactions
# ----------------------------------------
rows = get_day_book_transactions(financial_year_id, start_date, end_date)

data = []
for r in rows:
    txn_id = r[0]
    txn_date = r[1]
    narration = r[2]
    amount = float(r[3])
    from_id = r[4]
    from_acc = r[5]
    to_id = r[6]
    to_acc = r[7]

    data.append({
        "Txn ID": txn_id,
        "Date": txn_date,
        "Narration": narration,
        "From Account": from_acc,
        "To Account": to_acc,
        "Debit (₹)": amount,   # Debit = From Account
        "Credit (₹)": amount,  # Credit = To Account
        "Amount (₹)": amount
    })

df = pd.DataFrame(data)

with st.expander("### 📌 Day Book Transactions",expanded=False):

    if df.empty:
        st.warning("⚠️ No transactions found in selected date range.")
        st.stop()

    st.dataframe(df[["Txn ID", "Date", "Narration", "From Account", "To Account", "Amount (₹)"]], use_container_width=True)

# ✅ Method 1 (Best): Date Heading + Sub Table (Perfect Day Book Look)
with st.expander("### 📌 Day Book Transactions (Date Wise)", expanded=False):

    df = pd.DataFrame(data)

    if df.empty:
        st.warning("⚠️ No transactions found in selected date range.")
        st.stop()

    # Ensure proper date type
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Sort properly
    df = df.sort_values(["Date", "Txn ID"])

    # Group Date Wise
    for date_val, grp in df.groupby(df["Date"].dt.date):

        total_debit = grp["Debit (₹)"].sum()
        total_credit = grp["Credit (₹)"].sum()
        total_amount = grp["Amount (₹)"].sum()

        # Date Header
        st.markdown(f"""
        ## 📅 {date_val}

        ✅ **Total Debit:** ₹ {total_debit:,.2f} &nbsp;&nbsp;&nbsp;
        ✅ **Total Credit:** ₹ {total_credit:,.2f} &nbsp;&nbsp;&nbsp;
        💰 **Total Amount:** ₹ {total_amount:,.2f}
        """)

        # Transactions Table for that date
        st.dataframe(
            grp[["Txn ID", "Narration", "From Account", "To Account", "Amount (₹)"]],
            use_container_width=True
        )

        st.markdown("---")

# ✅ Method 2: Single Table but Date only on First Row (No Repeat)
with st.expander("### 📌 Day Book Transactions (Date Wise)", expanded=False):
    df = pd.DataFrame(data)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values(["Date", "Txn ID"])

    df["Date_Display"] = df["Date"].dt.strftime("%Y-%m-%d")

    # remove repeated date
    df.loc[df["Date_Display"].duplicated(), "Date_Display"] = ""

    st.dataframe(
        df[["Txn ID", "Date_Display", "Narration", "From Account", "To Account", "Amount (₹)"]],
        use_container_width=True
    )


# ----------------------------------------
# Date wise Daily Summary
# ----------------------------------------
st.markdown("---")
with st.expander("## 📅 Daily Summary (Date Wise Totals)", expanded=False):

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    daily_summary = df.groupby(df["Date"].dt.date).agg(
        Total_Transactions=("Txn ID", "count"),
        Total_Amount=("Amount (₹)", "sum")
    ).reset_index()

    daily_summary.rename(columns={"Date": "Txn Date"}, inplace=True)

    st.dataframe(daily_summary, use_container_width=True)

# ----------------------------------------
# Daily Chart
# ----------------------------------------
with st.expander("### 📊 Daily Total Amount Trend", expanded=False):

    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(daily_summary["Txn Date"], daily_summary["Total_Amount"], marker="o")

    ax1.set_xlabel("Date")
    ax1.set_ylabel("Amount (₹)")
    ax1.set_title("Day Book - Daily Total Amount")
    ax1.grid(True)

    plt.xticks(rotation=45)
    st.pyplot(fig1)

# ----------------------------------------
# Top 10 Debit Accounts (Payment Gone)
# ----------------------------------------
st.markdown("---")

with st.expander("## 🔻 Top 10 Debit Accounts (Most Payments Gone)", expanded=False):

    top_debit = df.groupby("From Account")["Amount (₹)"].sum().reset_index()
    top_debit = top_debit.sort_values("Amount (₹)", ascending=False).head(10)

    st.dataframe(top_debit, use_container_width=True)

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(top_debit["From Account"], top_debit["Amount (₹)"])
    ax2.set_title("Top 10 Debit Accounts (Payments)")
    ax2.set_xlabel("Account")
    ax2.set_ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# ----------------------------------------
# Top 10 Credit Accounts (Receipt Came)
# ----------------------------------------
st.markdown("---")
with st.expander("## 🔺 Top 10 Credit Accounts (Most Receipts Came)", expanded=False):

    top_credit = df.groupby("To Account")["Amount (₹)"].sum().reset_index()
    top_credit = top_credit.sort_values("Amount (₹)", ascending=False).head(10)

    st.dataframe(top_credit, use_container_width=True)

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    ax3.bar(top_credit["To Account"], top_credit["Amount (₹)"])
    ax3.set_title("Top 10 Credit Accounts (Receipts)")
    ax3.set_xlabel("Account")
    ax3.set_ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    st.pyplot(fig3)

# ----------------------------------------
# Professional Pie Chart (Top 5 + Others Combine)
# ----------------------------------------
st.markdown("---")
with st.expander("## 🥧 Top 5 Accounts Pie Chart (Others Combined)",expanded=False):

    all_accounts_flow = df.groupby("From Account")["Amount (₹)"].sum().reset_index()
    all_accounts_flow = all_accounts_flow.sort_values("Amount (₹)", ascending=False)

    top5 = all_accounts_flow.head(5)
    others_sum = all_accounts_flow.iloc[5:]["Amount (₹)"].sum()

    pie_labels = list(top5["From Account"])
    pie_values = list(top5["Amount (₹)"])

    if others_sum > 0:
        pie_labels.append("Others")
        pie_values.append(others_sum)

    fig4, ax4 = plt.subplots(figsize=(7, 7))
    ax4.pie(pie_values, labels=pie_labels, autopct="%1.1f%%", startangle=90)
    ax4.set_title("Top 5 Debit Accounts (Others Combined)")
    st.pyplot(fig4)

# ----------------------------------------
# Export Options
# ----------------------------------------
st.markdown("---")
with st.expander("### 💾 Export Options", expanded=False):
    colA, colB, colC = st.columns(3)

    # ---------- CSV ----------
    with colA:
        st.markdown("### 📄 CSV Export")

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name=f"day_book_{active_year['label']}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # ---------- Excel ----------
    with colB:
        st.markdown("### 📗 Excel Export")

        try:
            def to_excel_v2(df_main, df_daily, df_debit, df_credit):
                import io
                import pandas as pd

                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                    df_main.to_excel(writer, sheet_name="Day Book", index=False)
                    df_daily.to_excel(writer, sheet_name="Daily Summary", index=False)
                    df_debit.to_excel(writer, sheet_name="Top Debit", index=False)
                    df_credit.to_excel(writer, sheet_name="Top Credit", index=False)

                return output_buffer.getvalue()

            excel_data = to_excel_v2(df, daily_summary, top_debit, top_credit)

            st.download_button(
                "⬇️ Download Excel",
                data=excel_data,
                file_name=f"day_book_{active_year['label']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Excel export failed: {e}")

    # ---------- Print HTML ----------
    with colC:
        st.markdown("### 🖨 Print / PDF")

        print_html = f"""
        <html>
        <head>
            <title>Day Book Report</title>
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
            </style>
        </head>
        <body>
            <h2>Day Book Report</h2>

            <div class="summary">
                <b>Financial Year:</b> {active_year['label']}<br>
                <b>From:</b> {start_date} &nbsp;&nbsp; <b>To:</b> {end_date}<br><br>

                <b>Total Entries:</b> {summary['total_entries']}<br>
                <b>Total Amount:</b> ₹ {summary['total_amount']:,.2f}<br>
            </div>

            {df[["Txn ID","Date","Narration","From Account","To Account","Amount (₹)"]].to_html(index=False)}
        </body>
        </html>
        """

        st.download_button(
            "🖨 Download Print Report (HTML)",
            data=print_html.encode("utf-8"),
            file_name=f"day_book_{start_date}_{end_date}.html",
            mime="text/html",
            use_container_width=True
        )

        st.info("✅ Download HTML → Open in browser → CTRL+P → Save as PDF / Print")
