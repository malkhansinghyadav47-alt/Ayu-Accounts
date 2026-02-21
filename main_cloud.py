import os
import streamlit as st
from db_helpers import get_connection
from db_helpers import get_active_financial_year

st.set_page_config(page_title="Business Ledger", layout="wide")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📘 Business Ledger")

    active_year = get_active_financial_year()
    if active_year:
        st.success(f"🟢 Active Year : {active_year['label']}")
    else:
        st.warning("⚠️ No Active Year")

    st.markdown("---")

    # ---------------- DEFAULT SESSION INIT ----------------
    if "module_selection" not in st.session_state:
        st.session_state.module_selection = "💳 Transactions"

    if "report_selection" not in st.session_state:
        st.session_state.report_selection = "📑 Ledger Report"

    if "sidebar_section" not in st.session_state:
        st.session_state.sidebar_section = "📂 Input Modules"

    # ---------------- SIDEBAR CATEGORY SELECTOR ----------------
    st.session_state.sidebar_section = st.radio(
        "📌 Select Section",
        ["📂 Input Modules", "📂 Report Modules"],
        key="sidebar_section_radio"
    )

    st.markdown("---")

    # ---------------- INPUT MODULES ----------------
    input_menu_options = [
        "🏠 Dashboard",
        "📅 Financial Year",
        "🏷 Account Groups",
        "👤 Accounts",
        "💰 Opening Balance",
        "💳 Transactions"
    ]

    # ---------------- REPORT MODULES ----------------
    report_menu_options = [
        "📑 Ledger Report",
        "📊 Account Balances",
        "📊 Trial Balance",
        "📈 Profit & Loss",
        "🏦 Balance Sheet Progress Bar",
        "🏦 Balance Sheet No Loop",
        "💵 Cash Flow Report",
        "📒 Day Book Report",
        "📌 Outstanding Report",
        "📌 Group-wise Outstanding",
        "📋 Accounts List"
    ]

    module = None

    # ---------------- EXPANDER BASED MENU ----------------
    if st.session_state.sidebar_section == "📂 Input Modules":
        with st.expander("📂 Input Modules", expanded=True):
            module = st.radio(
                "Select Module",
                input_menu_options,
                key="module_selection"
            )

        with st.expander("📂 Report Modules", expanded=False):
            st.info("Select from Section menu above 👆")

    else:
        with st.expander("📂 Input Modules", expanded=False):
            st.info("Select from Section menu above 👆")

        with st.expander("📂 Report Modules", expanded=True):
            module = st.radio(
                "Select Report",
                report_menu_options,
                key="report_selection"
            )

    st.markdown("---")
    st.caption("⚡ Developed by:")
    st.caption("Ayuquant Software Pvt. Ltd. Ghaziabad, India.")
    st.caption("Jan Gan Man Public School, Muradnagar, Ghaziabad.")


# ---------------- MAIN PAGE ----------------

def main_cloud():
    # -------------------------------------------------
    # Main Screen Routing
    # -------------------------------------------------

    if module == "🏠 Dashboard":       
        file_path = "working_pages/00_dashboard.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 01_dashboard.py")

    elif module == "📅 Financial Year":
        file_path = "working_pages/01_fnancial_year.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 01_financial_year.py")

    elif module == "🏷 Account Groups":       
        file_path = "working_pages/02_groups.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 02_groups.py")
        
    elif module == "👤 Accounts":      
        file_path = "working_pages/03_accounts.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 03_accounts.py")
            
    elif module == "💰 Opening Balance":      
        file_path = "working_pages/04_opening_balance.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 04_opening_balance.py")       
            
    elif module == "💳 Transactions":
        file_path = "working_pages/05_transactions.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 04_opening_balance.py")       

    elif module == "📑 Ledger Report":
        file_path = "reports/ledger_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/ledger_report.py")

    elif module == "📊 Account Balances":
        file_path = "reports/account_balances_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/account_balances_report.py")


    elif module == "📊 Trial Balance":
        file_path = "reports/trial_balance_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/trial_balance_report.py")

    elif module == "📈 Profit & Loss":
        file_path = "reports/profit_loss_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/profit_loss_report.py")

    elif module == "🏦 Balance Sheet Progress Bar":
        file_path = "reports/balance_sheet_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/balance_sheet_report.py")

    elif module == "🏦 Balance Sheet No Loop":
        file_path = "reports/balance_sheet_report2.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/balance_sheet_report.py")

    elif module == "💵 Cash Flow Report":
        file_path = "reports/cash_flow_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/cash_flow_report.py")

    elif module == "📒 Day Book Report":
        file_path = "reports/day_book_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/day_book_report.py")

    elif module == "📌 Outstanding Report":
        file_path = "reports/outstanding_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/day_book_report.py")

    elif module == "📌 Group-wise Outstanding":
        file_path = "reports/groupwise_outstanding_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/day_book_report.py")

    elif module == "📋 Accounts List":
        file_path = "reports/accounts_list_report.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: reports/day_book_report.py")

if __name__ == "__main__":
    main_cloud()