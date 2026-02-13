import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from db_helpers import (
    get_connection,
    get_active_financial_year,
    format_amt,
    get_account_closing_balance
)

st.title("📒 Balance Sheet Report")

# -----------------------------------------
# Active Financial Year
# -----------------------------------------
active_year = get_active_financial_year()
if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

financial_year_id = active_year["id"]
fy_start = active_year["start_date"]
fy_end = active_year["end_date"]

st.success(f"🟢 Active Financial Year: {active_year['label']}")

# Convert FY start/end into date string usable
start_date = fy_start
end_date = fy_end


# -----------------------------------------
# Load Accounts + Groups
# -----------------------------------------
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, group_name FROM groups")
groups_data = cursor.fetchall()

group_dict = {g[0]: g[1] for g in groups_data}

cursor.execute("SELECT id, name, group_id FROM accounts")
accounts_data = cursor.fetchall()

conn.close()


if not accounts_data:
    st.warning("⚠️ No accounts found.")
    st.stop()


# -----------------------------------------
# Group Category Logic (By Group ID)
# -----------------------------------------
# ⚠️ IMPORTANT: You must set correct IDs according to your DB.
# Replace these IDs with your real group IDs.

ASSET_GROUP_IDS = [1, 2, 3, 4, 5]         # Example: Cash, Bank, Stock, Fixed Assets
LIABILITY_GROUP_IDS = [6, 7, 8, 9, 10]    # Example: Capital, Loans, Sundry Creditors

# -----------------------------------------
# Build Balance Sheet Data
# -----------------------------------------
assets_rows = []
liability_rows = []

total_assets = 0.0
total_liabilities = 0.0

progress = st.progress(0)
status = st.empty()

for i, (acc_id, acc_name, group_id) in enumerate(accounts_data):

    status.info(f"⏳ Calculating Balance: {acc_name}")

    closing = get_account_closing_balance(acc_id, financial_year_id, start_date, end_date)

    # Assets Side
    if group_id in ASSET_GROUP_IDS:
        assets_rows.append({
            "Account Name": acc_name,
            "Group": group_dict.get(group_id, "Unknown"),
            "Amount": round(closing, 2)
        })
        total_assets += closing

    # Liability Side
    elif group_id in LIABILITY_GROUP_IDS:
        liability_rows.append({
            "Account Name": acc_name,
            "Group": group_dict.get(group_id, "Unknown"),
            "Amount": round(closing, 2)
        })
        total_liabilities += closing

    progress.progress((i + 1) / len(accounts_data))


status.success("✅ Balance Sheet Generated Successfully")


# -----------------------------------------
# Convert to DataFrames
# -----------------------------------------
df_assets = pd.DataFrame(assets_rows)
df_liabilities = pd.DataFrame(liability_rows)

if df_assets.empty:
    df_assets = pd.DataFrame(columns=["Account Name", "Group", "Amount"])

if df_liabilities.empty:
    df_liabilities = pd.DataFrame(columns=["Account Name", "Group", "Amount"])


# -----------------------------------------
# Display Balance Sheet
# -----------------------------------------
st.divider()
st.subheader("📌 Balance Sheet")

col1, col2 = st.columns(2)

with col1:
    st.markdown("## 🏦 Assets")
    st.dataframe(df_assets, use_container_width=True)

    st.metric("Total Assets", format_amt(total_assets))

with col2:
    st.markdown("## 💳 Liabilities")
    st.dataframe(df_liabilities, use_container_width=True)

    st.metric("Total Liabilities", format_amt(total_liabilities))


# -----------------------------------------
# Balance Check
# -----------------------------------------
st.divider()
diff = abs(total_assets - total_liabilities)

if diff < 0.01:
    st.success("✅ Balance Sheet Matched (Assets = Liabilities)")
else:
    st.error(f"❌ Not Balanced! Difference = {format_amt(diff)}")


# -----------------------------------------
# Export Section
# -----------------------------------------
st.divider()
st.subheader("📥 Export Options")

colA, colB = st.columns(2)

# CSV Export
with colA:
    st.markdown("### 📄 CSV Export")

    export_df = pd.concat([
        pd.DataFrame([{"---": "ASSETS"}]),
        df_assets,
        pd.DataFrame([{"---": "LIABILITIES"}]),
        df_liabilities
    ], ignore_index=True)

    csv_data = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Balance Sheet CSV",
        data=csv_data,
        file_name=f"balance_sheet_{active_year['label']}.csv",
        mime="text/csv",
        use_container_width=True
    )


# Excel Export
with colB:
    st.markdown("### 📗 Excel Export")

    try:
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_assets.to_excel(writer, sheet_name="Assets", index=False)
            df_liabilities.to_excel(writer, sheet_name="Liabilities", index=False)

        st.download_button(
            "⬇️ Download Balance Sheet Excel",
            data=output.getvalue(),
            file_name=f"balance_sheet_{active_year['label']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"❌ Excel Export Failed: {e}")
