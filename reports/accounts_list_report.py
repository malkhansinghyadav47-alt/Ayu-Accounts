import streamlit as st
import pandas as pd
from io import BytesIO

from db_helpers import (
    get_active_financial_year,
    get_accounts_list,
    get_group_summary_opening
)

st.title("📋 Accounts List")

# -----------------------------
# Active Financial Year
# -----------------------------
active_year = get_active_financial_year()

if not active_year:
    st.error("❌ No Active Financial Year Found.")
    st.stop()

financial_year_id = active_year["id"]

st.success(f"🟢 Active FY: {active_year['label']}")

# -----------------------------
# Report Mode Selection
# -----------------------------
st.markdown("---")
with st.expander("### 📌 Accounts View", expanded=False):

    view_mode = st.radio(
        "Choose Report Type:",
        [
            "All Accounts (Alphabetical)",
            "Group-wise Accounts (Group + Account Alphabetical)",
            "Group Summary (Opening Balance Totals)"
        ],
        horizontal=True
    )

    # -----------------------------
    # Load Data Based on Mode
    # -----------------------------
    if view_mode == "All Accounts (Alphabetical)":
        rows = get_accounts_list(financial_year_id, mode="ALL")

    elif view_mode == "Group-wise Accounts (Group + Account Alphabetical)":
        rows = get_accounts_list(financial_year_id, mode="GROUP")

    else:
        rows = get_group_summary_opening(financial_year_id)

    if not rows:
        st.warning("⚠️ No records found.")
        st.stop()

    # -----------------------------
    # Prepare DataFrame
    # -----------------------------
    data = []

    if view_mode != "Group Summary (Opening Balance Totals)":

        for r in rows:
            acc_id = r[0]
            acc_name = r[1]
            group_name = r[2] if r[2] else "No Group"
            opening_amount = float(r[3]) if r[3] else 0

            opening_dr = opening_amount if opening_amount > 0 else 0
            opening_cr = abs(opening_amount) if opening_amount < 0 else 0

            data.append({
                "ID": acc_id,
                "Account Name": acc_name,
                "Group": group_name,
                "Opening Dr (₹)": opening_dr,
                "Opening Cr (₹)": opening_cr,
                "Net Opening (₹)": opening_amount
            })

        df = pd.DataFrame(data)

    else:
        for r in rows:
            group_name = r[0] if r[0] else "No Group"
            total_opening = float(r[1]) if r[1] else 0

            opening_dr = total_opening if total_opening > 0 else 0
            opening_cr = abs(total_opening) if total_opening < 0 else 0

            data.append({
                "Group Name": group_name,
                "Total Opening Dr (₹)": opening_dr,
                "Total Opening Cr (₹)": opening_cr,
                "Net Opening (₹)": total_opening
            })

        df = pd.DataFrame(data)

    # -----------------------------
    # Search Filter
    # -----------------------------
    st.markdown("---")

    if view_mode != "Group Summary (Opening Balance Totals)":
        search = st.text_input("🔍 Search Account Name")

        if search:
            df = df[df["Account Name"].str.contains(search, case=False, na=False)]

    # -----------------------------
    # Show Table
    # -----------------------------
    st.markdown("### 📌 Accounts List")
    st.dataframe(df, use_container_width=True)

# -----------------------------
# Export Options
# -----------------------------
st.markdown("---")
with st.expander("### 📤 Export Options", expanded=False):
    colA, colB, colC = st.columns(3)

    # CSV Export
    with colA:
        st.markdown("### 📄 CSV Export")
        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name=f"accounts_list_{active_year['label']}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Excel Export
    with colB:
        st.markdown("### 📗 Excel Export")

        try:
            import io

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Accounts List", index=False)

            st.download_button(
                "⬇️ Download Excel",
                data=output.getvalue(),
                file_name=f"accounts_list_{active_year['label']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Excel Export Failed: {e}")

    # Print HTML Export
    with colC:
        st.markdown("### 🖨 Print / PDF")

        if not df.empty:
            print_html = f"""
            <html>
            <head>
                <title>Accounts List</title>
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
                        margin-top: 15px;
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
                <h2>Accounts List Report</h2>
                <h4 style="text-align:center;color:gray;">
                    Financial Year: {active_year['label']}
                </h4>

                {df.to_html(index=False)}
            </body>
            </html>
            """

            st.download_button(
                "🖨 Download Print Report (HTML)",
                data=print_html.encode("utf-8"),
                file_name=f"accounts_list_{active_year['label']}.html",
                mime="text/html",
                use_container_width=True
            )

            st.info("✅ Download HTML → Open in browser → CTRL+P")

        else:
            st.button("🖨 Download Print Report (HTML)", use_container_width=True, disabled=True)
