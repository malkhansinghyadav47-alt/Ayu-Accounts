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

    # ✅ Capture values into variables
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):

        if not username or not password:
            st.warning("Please enter username and password")
            return

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

        if st.button("Logout", key="logout_button"):
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

        # -------------------------
        # Section Selector
        # -------------------------
        sections = ["📂 Input Modules", "📊 Report Modules"]

        if st.session_state.role_name == "Admin":
            sections.append("⚙️ Admin Modules")

        section = st.radio(
            "📌 Select Section",
            sections,
            key="sidebar_section"
        )

        st.markdown("---")

        # -------------------------
        # INPUT MODULES
        # -------------------------
        if section == "📂 Input Modules":

            input_menu_options = [
                "🏠 Dashboard",
                "📅 Financial Year",
                "🏷 Account Groups",
                "👤 Accounts",
                "💰 Opening Balance",
                "💳 Transactions"
            ]

            module = st.radio(
                "Select Module",
                input_menu_options,
                key="input_module_radio"
            )

        # -------------------------
        # REPORT MODULES
        # -------------------------
        elif section == "📊 Report Modules":

            report_menu_options = [
                "📑 Ledger",
                "📊 Trial Balance",
                "📊 Account Balances",
                "📈 Profit & Loss",
                "🏦 Balance Sheet",
                "💵 Cash Flow",
                "📒 Day Book",
                "📌 Party Outstandings",
                "📌 Group Outstandings",
                "📋 Accounts List"
            ]

            module = st.radio(
                "Select Report",
                report_menu_options,
                key="report_module_radio"
            )

        # -------------------------
        # ADMIN MODULES
        # -------------------------
        elif section == "⚙️ Admin Modules":

            admin_menu_options = [
                "🔐 Users Management",
                "💾 Backup Management"
            ]

            module = st.radio(
                "Select Admin Module",
                admin_menu_options,
                key="admin_module_radio"
            )

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

        "🔐 Users Management": "working_pages/06_users_management.py",
        "💾 Backup Management": "working_pages/07_backup_management.py",
        
        "🏠 Dashboard": "working_pages/00_dashboard.py",
        "📅 Financial Year": "working_pages/01_fnancial_year.py",
        "🏷 Account Groups": "working_pages/02_groups.py",
        "👤 Accounts": "working_pages/03_accounts.py",
        "💰 Opening Balance": "working_pages/04_opening_balance.py",
        "💳 Transactions": "working_pages/05_transactions.py",

        "📑 Ledger": "reports/ledger_report.py",
        "📊 Trial Balance": "reports/trial_balance_report.py",
        "📊 Account Balances": "reports/account_balances_report.py",
        "📈 Profit & Loss": "reports/profit_loss_report.py",
        "🏦 Balance Sheet": "reports/balance_sheet_report2.py",
        "💵 Cash Flow": "reports/cash_flow_report.py",
        "📒 Day Book": "reports/day_book_report.py",
        "📌 Party Outstandings": "reports/outstanding_report.py",
        "📌 Group Outstandings": "reports/groupwise_outstanding_report.py",
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