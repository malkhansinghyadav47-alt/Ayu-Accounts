import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from db_helpers import (
    get_active_financial_year,
    format_amt,
    get_all_balances_optimized
)

st.set_page_config(page_title="Balance Sheet", layout="wide")
st.title("📒 Balance Sheet Report")

active_year = get_active_financial_year()
if not active_year:
    st.error("❌ No active financial year selected.")
    st.stop()

financial_year_id = active_year["id"]
fy_start = active_year["start_date"]
fy_end = active_year["end_date"]

st.success(f"🟢 Active Financial Year: {active_year['label']}")

# --- CONFIGURATION ---
ASSET_GROUP_IDS = [1, 2, 3, 4, 5] 
LIABILITY_GROUP_IDS = [6, 7, 8, 9, 10]
INCOME_GROUP_IDS = [11, 12]
EXPENSE_GROUP_IDS = [13, 14]

# --- 1. FILTERS (Now on the Main Page instead of Sidebar) ---
# We use st.columns to keep the filters neatly lined up at the top
col_v, col_s, col_e = st.columns([2, 1, 1])

with col_v:
    view_type = st.radio(
        "Select View Level", 
        ["Summary (Groups)", "Detailed (Accounts)"],
        key="bs_main_view_toggle", # Unique key to prevent duplication errors
        horizontal=True # Makes it look cleaner on the main page
    )

with col_s:
    start_dt = st.date_input(
        "Start Date", 
        value=datetime.strptime(active_year["start_date"], "%Y-%m-%d"),
        key="bs_main_start_date" # Unique key
    )

with col_e:
    end_dt = st.date_input(
        "End Date", 
        value=datetime.strptime(active_year["end_date"], "%Y-%m-%d"),
        key="bs_main_end_date" # Unique key
    )

# --- 2. DATA CALCULATION (Runs automatically when any filter changes) ---
df_raw = get_all_balances_optimized(
    active_year["id"], 
    start_dt.strftime("%Y-%m-%d"), 
    end_dt.strftime("%Y-%m-%d")
)

if df_raw.empty:
    st.warning("⚠️ No transactions found for the selected date range.")
else:
    # Calculate Net Profit
    total_inc = df_raw[df_raw['group_id'].isin(INCOME_GROUP_IDS)]['balance'].sum()
    total_exp = df_raw[df_raw['group_id'].isin(EXPENSE_GROUP_IDS)]['balance'].sum()
    net_profit = (total_inc * -1) - total_exp 

    # Filter Assets & Liabilities
    df_assets = df_raw[df_raw['group_id'].isin(ASSET_GROUP_IDS)].copy()
    df_liabs = df_raw[df_raw['group_id'].isin(LIABILITY_GROUP_IDS)].copy()
    
    # --- 3. APPLY TOGGLE LOGIC ---
    if view_type == "Summary (Groups)":
        # Group data by the 'group_name' column
        disp_assets = df_assets.groupby("group_name")["balance"].sum().reset_index()
        disp_liabs = df_liabs.groupby("group_name")["balance"].sum().reset_index()
        disp_assets.columns = ["Group Name", "Total Balance"]
        disp_liabs.columns = ["Group Name", "Total Balance"]
    else:
        # Show individual accounts
        disp_assets = df_assets[["acc_name", "group_name", "balance"]]
        disp_liabs = df_liabs[["acc_name", "group_name", "balance"]]

    # Add Net Profit to Liability/Equity side
    profit_row = pd.DataFrame({
        disp_liabs.columns[0]: ["Net Profit / (Loss)"], 
        disp_liabs.columns[-1]: [net_profit]
    })
    disp_liabs = pd.concat([disp_liabs, profit_row], ignore_index=True)

    # Calculate Metrics
    total_assets = df_assets['balance'].sum()
    total_liab_equity = df_liabs['balance'].sum() + net_profit

    # --- 4. DISPLAY ---
    st.divider()
    st.info(f"📊 Viewing **{view_type}** for period {start_dt} to {end_dt}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏦 Assets")
        st.dataframe(disp_assets, use_container_width=True, hide_index=True)
        st.metric("Total Assets", format_amt(total_assets))

    with col2:
        st.subheader("💳 Liabilities & Equity")
        st.dataframe(disp_liabs, use_container_width=True, hide_index=True)
        st.metric("Total Liab & Equity", format_amt(total_liab_equity))

    # --- 5. EXCEL EXPORT ---
    st.divider()
    # Note: We put the export at the bottom so it's always available
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        disp_assets.to_excel(writer, sheet_name="Assets", index=False)
        disp_liabs.to_excel(writer, sheet_name="Liabilities_Equity", index=False)
    
    st.download_button(
        label="📗 Download Excel Report",
        data=output.getvalue(),
        file_name=f"Balance_Sheet_{end_dt}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )