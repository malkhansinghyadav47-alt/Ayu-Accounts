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
    
    st.markdown("### 📂 Modules")

    # Define the list once
    menu_options = [
        "🏠 Dashboard", 
        "📅 Financial Year", 
        "🏷 Account Groups", 
        "👤 Accounts", 
        "💰 Opening Balance", 
        "💳 Transactions"
    ]

    # Initialize the default value in session state BEFORE the widget
    if "module_selection" not in st.session_state:
        st.session_state.module_selection = "💳 Transactions"

    # Use 'key' to link the radio directly to session_state
    # This removes the need for 'index=' logic and fixes the double-click bug
    module = st.radio(
        "Select Module",
        menu_options,
        key="module_selection" 
    )

# ---------------- MAIN PAGE ----------------

def main_cloud():
    # -------------------------------------------------
    # Main Screen Routing
    # -------------------------------------------------

    if module == "🏠 Dashboard":
        st.title("📘 Business Ledger System")
        st.subheader("🏠 Dashboard")
        st.info("Here we will show summary, balances, charts later.")

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
        file_path = "working_pages/04_transactions.py"

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                exec(f.read())
        else:
            st.error("❌ File not found: 04_opening_balance.py")       

if __name__ == "__main__":
    main_cloud()