import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse


from db_helpers import (
    get_active_financial_year,
    get_all_accounts,
    get_opening_balance,
    get_account_ledger,
    calculate_running_ledger
)

st.set_page_config(page_title="Trial Balance Report", layout="wide")

st.title("📊 Trial Balance")

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
if not accounts:
    st.warning("⚠️ No accounts found.")
    st.stop()

# -----------------------------
# 3. Trial Balance Calculation
# -----------------------------
trial_rows = []
total_debit = 0.0
total_credit = 0.0

progress = st.progress(0)
status_text = st.empty()

for i, acc in enumerate(accounts):
    status_text.info(f"⏳ Calculating: {acc['name']}")

    opening = get_opening_balance(acc["id"], financial_year_id)

    ledger_rows = get_account_ledger(
        acc["id"],
        financial_year_id,
        fy_start.strftime("%Y-%m-%d"),
        fy_end.strftime("%Y-%m-%d")
    )

    ledger_data, total_dr, total_cr, closing = calculate_running_ledger(ledger_rows, opening)

    dr_amt = 0.0
    cr_amt = 0.0

    if closing >= 0:
        dr_amt = abs(closing)
    else:
        cr_amt = abs(closing)

    total_debit += dr_amt
    total_credit += cr_amt

    trial_rows.append({
        "Account Name": acc["name"],
        "Debit (Dr)": round(dr_amt, 2),
        "Credit (Cr)": round(cr_amt, 2)
    })

    progress.progress((i + 1) / len(accounts))

status_text.success("✅ Trial Balance Generated Successfully")

df = pd.DataFrame(trial_rows)

# -----------------------------
# 4. Display Table
# -----------------------------
st.subheader("📌 Trial Balance Table")

st.dataframe(df, use_container_width=True)

# -----------------------------
# 5. Totals Section
# -----------------------------
st.divider()
st.subheader("📊 Totals Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Debit (Dr)", f"₹ {total_debit:,.2f}")
col2.metric("Total Credit (Cr)", f"₹ {total_credit:,.2f}")

diff = abs(total_debit - total_credit)

if diff < 0.01:
    col3.success("✅ Balanced (Dr = Cr)")
else:
    col3.error(f"❌ Not Balanced (Diff: ₹ {diff:,.2f})")

# -----------------------------
# 6. Export Options
# -----------------------------
st.divider()
st.subheader("📥 Export Options")

with st.expander("Printing & Sharing Options"):
    colA, colB, colC = st.columns(3)

    # CSV Download
    csv_data = df.to_csv(index=False).encode("utf-8")
    colA.download_button(
        "⬇️ Download CSV",
        data=csv_data,
        file_name=f"trial_balance_{active_year['label']}.csv",
        mime="text/csv",
        use_container_width=True
    )

    with colB:
        st.divider()
    st.subheader("📲 Share on WhatsApp")

    wa_message = f"""
    📊 Trial Balance Report
    Financial Year: {active_year['label']}

    Total Debit (Dr): ₹ {total_debit:,.2f}
    Total Credit (Cr): ₹ {total_credit:,.2f}
    Difference: ₹ {diff:,.2f}

    Generated from Business Ledger System
    """

    wa_text = urllib.parse.quote(wa_message)

    wa_link = f"https://wa.me/?text={wa_text}"

    st.markdown(
        f"""
        <a href="{wa_link}" target="_blank">
            <button style="
                width:100%;
                padding:12px;
                font-size:16px;
                font-weight:bold;
                border:none;
                border-radius:8px;
                background:#25D366;
                color:white;
                cursor:pointer;
            ">
            📲 Share Trial Balance on WhatsApp
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )  

    # -----------------------------
    # 7. Print Option (A4 HTML)
    # -----------------------------
    with colC:
        st.markdown("### 🖨 Print Trial Balance")

        if not df.empty:

            print_html = f"""
            <html>
            <head>
                <title>Trial Balance Report</title>
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
                <h2>Trial Balance Report</h2>

                <div class="summary">
                    <b>Financial Year:</b> {active_year['label']}<br><br>

                    <b>Total Debit (Dr):</b> ₹ {total_debit:,.2f}<br>
                    <b>Total Credit (Cr):</b> ₹ {total_credit:,.2f}<br>
                    <b>Difference:</b> ₹ {diff:,.2f}<br>
                </div>

                {df.to_html(index=False)}
            </body>
            </html>
            """

            st.download_button(
                "🖨 Download Print Trial Balance (HTML)",
                data=print_html.encode("utf-8"),
                file_name=f"Trial_Balance_{active_year['label']}.html",
                mime="text/html",
                use_container_width=True
            )

            st.info("✅ Download HTML file → Open it in browser → Press CTRL+P to Print")

        else:
            st.button("🖨 Download Print Trial Balance (HTML)", use_container_width=True, disabled=True)
