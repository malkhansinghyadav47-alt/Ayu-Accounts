import sqlite3
import streamlit as st

from db_helpers import (
    get_active_financial_year,
    get_all_financial_years,
    set_active_financial_year,
    indian_date
)

st.set_page_config(page_title="Financial Year Setup", layout="wide")

st.title("📅 Financial Year Management")

# -------------------------------
# Show Current Active Year
# -------------------------------
active_year = get_active_financial_year()

st.subheader("🔁 Current Active Financial Year")

if active_year:
    st.success(
        f"Active Year: {active_year['label']}  "
        f"({indian_date(active_year['start_date'])} to {indian_date(active_year['end_date'])})" # Indian date format
    )
else:
    st.warning("⚠️ No active financial year selected!")

st.divider()

# -------------------------------
# Switch Active Year
# -------------------------------
st.subheader("🔀 Change Active Financial Year")

years = get_all_financial_years()

if not years:
    st.error("No financial years found in database.")
    st.stop()

year_labels = [y["label"] for y in years]
year_map = {y["label"]: y["id"] for y in years}

selected_label = st.selectbox("Select Financial Year", year_labels)

if st.button("Set As Active Year"):
    year_id = year_map[selected_label]
    set_active_financial_year(year_id)
    st.success(f"✅ Financial Year {selected_label} is now Active")
    st.rerun()

st.divider()

# -------------------------------
# Display All Financial Years
# -------------------------------
st.subheader("📋 All Financial Years")

table_data = []
for y in years:
    table_data.append({
        "Year": y["label"],
        "Start": indian_date(y["start_date"]), # Indian date format
        "End": indian_date(y["end_date"]),
        "Active": "✅" if y["is_active"] == 1 else ""
    })

st.dataframe(table_data, use_container_width=True)
