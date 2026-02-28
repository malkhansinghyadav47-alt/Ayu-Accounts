import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from db_helpers import (
    get_active_financial_year,
    get_groupwise_outstanding,
    get_group_outstanding_accounts
)

st.title("📌 Group-wise Outstanding Report")
st.markdown("### Sundry Debtors / Sundry Creditors Style")

active_year = get_active_financial_year()

if not active_year:
    st.warning("⚠️ No Active Financial Year Found.")
    st.stop()

financial_year_id = active_year["id"]

# ----------------------------------------
# Date Filters
# ----------------------------------------
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("📅 Start Date", value=datetime.strptime(active_year["start_date"], "%Y-%m-%d"))

with col2:
    end_date = st.date_input("📅 End Date", value=datetime.strptime(active_year["end_date"], "%Y-%m-%d"))

start_date = start_date.strftime("%Y-%m-%d")
end_date = end_date.strftime("%Y-%m-%d")

# ----------------------------------------
# Group-wise Summary
# ----------------------------------------
group_rows = get_groupwise_outstanding(financial_year_id, start_date, end_date)

df_groups = pd.DataFrame(group_rows)

if df_groups.empty:
    st.warning("⚠️ No outstanding data found.")
    st.stop()

st.markdown("---")
with st.expander("## 📌 Group Summary View", False):

    st.dataframe(df_groups, use_container_width=True)

# Totals
total_receivable = df_groups["Receivable (Dr)"].sum()
total_payable = df_groups["Payable (Cr)"].sum()

c1, c2, c3 = st.columns(3)

c1.success(f"📥 Total Receivable\n\n₹ {total_receivable:,.2f}")
c2.error(f"📤 Total Payable\n\n₹ {total_payable:,.2f}")
c3.info(f"⚖ Net Outstanding\n\n₹ {(total_receivable - total_payable):,.2f}")

# ----------------------------------------
# Drill Down Group Details
# ----------------------------------------
st.markdown("---")
with st.expander("## 🔍 Group Detail View", expanded=False):

    group_dict = {f"{row['Group Name']} (ID:{row['Group ID']})": row["Group ID"] for row in group_rows}

    selected_group = st.selectbox("📌 Select Group to View Accounts", list(group_dict.keys()))
    selected_group_id = group_dict[selected_group]

    acc_rows = get_group_outstanding_accounts(selected_group_id, financial_year_id, start_date, end_date)
    df_accounts = pd.DataFrame(acc_rows)

    st.markdown(f"### 📌 Accounts in: {selected_group}")

    if df_accounts.empty:
        st.warning("⚠️ No accounts outstanding in this group.")
    else:
        st.dataframe(df_accounts, use_container_width=True)

# ----------------------------------------
# Export Options
# ----------------------------------------
st.markdown("---")
with st.expander("📤 Export Options", expanded=False):
    colA, colB, colC = st.columns(3)

    # CSV Export
    with colA:
        csv_data = df_groups.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Group CSV",
            data=csv_data,
            file_name=f"groupwise_outstanding_{active_year['label']}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Excel Export
    with colB:
        try:
            def to_excel_v2(df1, df2):
                import io
                import pandas as pd

                output = io.BytesIO()

                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df1.to_excel(writer, sheet_name="Group Summary", index=False)
                    df2.to_excel(writer, sheet_name="Selected Group Accounts", index=False)

                return output.getvalue()

            excel_data = to_excel_v2(df_groups, df_accounts)

            st.download_button(
                "⬇️ Download Excel",
                data=excel_data,
                file_name=f"groupwise_outstanding_{active_year['label']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Excel export failed: {e}")

    # Print HTML
    with colC:
        if not df_groups.empty:
            print_html = f"""
            <html>
            <head>
                <title>Group-wise Outstanding</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        padding: 20px;
                    }}
                    h2 {{
                        text-align: center;
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
                <h2>Group-wise Outstanding Report</h2>

                <p><b>Financial Year:</b> {active_year['label']}</p>
                <p><b>From:</b> {start_date} &nbsp;&nbsp; <b>To:</b> {end_date}</p>

                <h3>Group Summary</h3>
                {df_groups.to_html(index=False)}

                <h3>Selected Group Accounts</h3>
                {df_accounts.to_html(index=False)}

            </body>
            </html>
            """

            st.download_button(
                "🖨 Download Print Report (HTML)",
                data=print_html.encode("utf-8"),
                file_name=f"groupwise_outstanding_{active_year['label']}.html",
                mime="text/html",
                use_container_width=True
            )
