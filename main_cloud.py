import os
import streamlit as st
from db_helpers import (
    get_connection,
    verify_password,
    get_active_financial_year
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Business Ledger", layout="wide")


# -------------------------------------------------
# LOGIN SCREEN
# -------------------------------------------------
def login_screen():
    st.title("Ayuquant Accounts Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = get_connection()
        user = conn.execute("""
            SELECT u.*, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = ? AND u.is_active = 1
        """, (username,)).fetchone()

        if user and verify_password(password, user["password_hash"]):
            st.session_state.user_id = user["id"]
            st.session_state.username = user["username"]
            st.session_state.role_id = user["role_id"]
            st.session_state.role_name = user["role_name"]

            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")


# -------------------------------------------------
# SIDEBAR (ONLY AFTER LOGIN)
# -------------------------------------------------
def load_sidebar():

    with st.sidebar:

        st.write(f"👤 Logged in as: {st.session_state.username}")

        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.title("📘 Business Ledger")

        active_year = get_active_financial_year()
        if active_year:
            st.success(f"🟢 Active Year : {active_year['label']}")
        else:
            st.warning("⚠️ No Active Year")

        st.markdown("---")

        # Default session values
        if "module_selection" not in st.session_state:
            st.session_state.module_selection = "💳 Transactions"

        if "report_selection" not in st.session_state:
            st.session_state.report_selection = "📑 Ledger Report"

        if "sidebar_section" not in st.session_state:
            st.session_state.sidebar_section = "📂 Input Modules"

        # Section Selector
        section = st.radio(
            "📌 Select Section",
            ["📂 Input Modules", "📂 Report Modules"],
        )

        st.markdown("---")

        # Input Modules
        input_menu_options = [
            "🏠 Dashboard",
            "📅 Financial Year",
            "🏷 Account Groups",
            "👤 Accounts",
            "💰 Opening Balance",
            "💳 Transactions"
        ]

        # Show User Management only to Admin
        if st.session_state.role_name == "Admin":
            input_menu_options.insert(0, "User Management")

        # Report Modules
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

        if section == "📂 Input Modules":
            module = st.radio("Select Module", input_menu_options)
        else:
            module = st.radio("Select Report", report_menu_options)

        st.markdown("---")
        st.caption("⚡ Developed by:")
        st.caption("Ayuquant Software Pvt. Ltd. Ghaziabad, India.")
        st.caption("Jan Gan Man Public School, Muradnagar, Ghaziabad.")

        return module


# -------------------------------------------------
# MAIN ROUTING
# -------------------------------------------------
def load_module(module):

    routing = {

        "User Management": "working_pages/6_User_Management.py",
        "🏠 Dashboard": "working_pages/00_dashboard.py",
        "📅 Financial Year": "working_pages/01_fnancial_year.py",
        "🏷 Account Groups": "working_pages/02_groups.py",
        "👤 Accounts": "working_pages/03_accounts.py",
        "💰 Opening Balance": "working_pages/04_opening_balance.py",
        "💳 Transactions": "working_pages/05_transactions.py",

        "📑 Ledger Report": "reports/ledger_report.py",
        "📊 Account Balances": "reports/account_balances_report.py",
        "📊 Trial Balance": "reports/trial_balance_report.py",
        "📈 Profit & Loss": "reports/profit_loss_report.py",
        "🏦 Balance Sheet Progress Bar": "reports/balance_sheet_report.py",
        "🏦 Balance Sheet No Loop": "reports/balance_sheet_report2.py",
        "💵 Cash Flow Report": "reports/cash_flow_report.py",
        "📒 Day Book Report": "reports/day_book_report.py",
        "📌 Outstanding Report": "reports/outstanding_report.py",
        "📌 Group-wise Outstanding": "reports/groupwise_outstanding_report.py",
        "📋 Accounts List": "reports/accounts_list_report.py",
    }

    file_path = routing.get(module)

    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            exec(f.read())
    else:
        st.error(f"❌ File not found: {file_path}")


# -------------------------------------------------
# MAIN APP
# -------------------------------------------------
def main_cloud():

    # Authentication Check
    if "user_id" not in st.session_state:
        login_screen()
        return

    module = load_sidebar()
    load_module(module)


# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":
    main_cloud()