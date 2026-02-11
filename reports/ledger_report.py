import streamlit as st
import pandas as pd
from datetime import datetime, date
import urllib.parse
import base64

from db_helpers import (
    get_active_financial_year,
    get_all_accounts,
    get_opening_balance,
    get_account_ledger,
    calculate_running_ledger
)

st.title("📒 Ledger Report")

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
# 2. Load Accounts
# -----------------------------
accounts = get_all_accounts()

acc_dict = {f"{a['name']} (ID:{a['id']})": a["id"] for a in accounts}

selected_acc = st.selectbox("Select Account", list(acc_dict.keys()))
account_id = acc_dict[selected_acc]

# Extract Account Name (for report titles)
selected_acc_name = selected_acc.split(" (ID:")[0].strip()

# -----------------------------
# 3. Date Filter (Inside FY)
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
# 4. Opening Balance
# -----------------------------
opening = get_opening_balance(account_id, financial_year_id)

if opening >= 0:
    opening_text = f"{opening:.2f} Dr"
else:
    opening_text = f"{abs(opening):.2f} Cr"

st.info(f"Opening Balance: **{opening_text}**")

# -----------------------------
# 5. Fetch Ledger
# -----------------------------
ledger_rows = get_account_ledger(
    account_id,
    financial_year_id,
    start_date.strftime("%Y-%m-%d"),
    end_date.strftime("%Y-%m-%d")
)

ledger_data, total_dr, total_cr, closing = calculate_running_ledger(ledger_rows, opening)

df = pd.DataFrame(ledger_data)

st.subheader("📌 Ledger Entries")

if df.empty:
    st.warning("No transactions found.")
else:
    st.dataframe(df, use_container_width=True)

# -----------------------------
# 6. Summary
# -----------------------------
st.subheader("📊 Summary")

if closing >= 0:
    closing_text = f"{closing:.2f} Dr"
else:
    closing_text = f"{abs(closing):.2f} Cr"

c1, c2, c3 = st.columns(3)
c1.metric("Total Debit", f"{total_dr:.2f}")
c2.metric("Total Credit", f"{total_cr:.2f}")
c3.metric("Closing Balance", closing_text)

# -----------------------------
# 7. REPORT ACTIONS (PRINT / EXCEL / WHATSAPP)
# -----------------------------
st.divider()
st.subheader("🧾 Report Actions")

# Prepare report text summary
ledger_summary = f"""
📒 Ledger Report
Account: {selected_acc_name}
Financial Year: {active_year['label']}
From: {start_date.strftime('%d-%m-%Y')}
To: {end_date.strftime('%d-%m-%Y')}

Opening Balance: {opening_text}
Total Debit: {total_dr:.2f}
Total Credit: {total_cr:.2f}
Closing Balance: {closing_text}
""".strip()

colA, colB, colC = st.columns([1, 1, 2])

# -----------------------------
# EXCEL DOWNLOAD
# -----------------------------
with colA:
    if not df.empty:
        excel_df = df.copy()
        excel_bytes = excel_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Excel (CSV)",
            data=excel_bytes,
            file_name=f"Ledger_{selected_acc_name}_{start_date}_{end_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.download_button(
            "⬇️ Download Excel (CSV)",
            data="",
            file_name="ledger.csv",
            mime="text/csv",
            disabled=True,
            use_container_width=True
        )

# -----------------------------
# PRINT BUTTON
# -----------------------------
# -----------------------------
# PRINT BUTTON (FIXED - WORKING)
# -----------------------------
with colB:
    if not df.empty:
        print_html = f"""
        <html>
        <head>
            <title>Ledger Report</title>
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
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h2>Ledger Report</h2>
            <div class="summary">
                <b>Account:</b> {selected_acc_name}<br>
                <b>Financial Year:</b> {active_year['label']}<br>
                <b>From:</b> {start_date.strftime('%d-%m-%Y')} &nbsp;&nbsp;
                <b>To:</b> {end_date.strftime('%d-%m-%Y')}<br><br>

                <b>Opening Balance:</b> {opening_text}<br>
                <b>Total Debit:</b> {total_dr:.2f}<br>
                <b>Total Credit:</b> {total_cr:.2f}<br>
                <b>Closing Balance:</b> {closing_text}<br>
            </div>

            {df.to_html(index=False)}
        </body>
        </html>
        """

        st.download_button(
            "🖨 Download Print Ledger (HTML)",
            data=print_html.encode("utf-8"),
            file_name=f"Ledger_{selected_acc_name}_{start_date}_{end_date}.html",
            mime="text/html",
            use_container_width=True
        )

        st.info("✅ Download HTML file → Open it in browser → Press CTRL+P to Print")
    else:
        st.button("🖨 Download Print Ledger (HTML)", use_container_width=True, disabled=True)

# -----------------------------
# WHATSAPP MESSAGE
# -----------------------------
with colC:
    whatsapp_no = st.text_input("📲 WhatsApp Number (with country code)", placeholder="91XXXXXXXXXX")

    if st.button("🟢 Send Summary to WhatsApp", use_container_width=True):
        if not whatsapp_no.strip():
            st.error("❌ Please enter WhatsApp number.")
            st.stop()

        msg = urllib.parse.quote(ledger_summary)
        wa_url = f"https://wa.me/{whatsapp_no.strip()}?text={msg}"

        st.success("✅ WhatsApp ready. Click below:")
        st.markdown(f"### 👉 [Open WhatsApp Chat]({wa_url})", unsafe_allow_html=True)
