import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from db_helpers import (
    get_active_financial_year,
    get_outstanding_report
)

st.title("📌 Outstanding Report")
st.markdown("### Receivable / Payable Summary")
with st.expander("## Select Date Range", expanded=False):
    active_year = get_active_financial_year()

    if not active_year:
        st.warning("⚠️ No Active Financial Year Found.")
        st.stop()

    financial_year_id = active_year["id"]

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("📅 Start Date", value=datetime.strptime(active_year["start_date"], "%Y-%m-%d"))

    with col2:
        end_date = st.date_input("📅 End Date", value=datetime.strptime(active_year["end_date"], "%Y-%m-%d"))

    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

# ----------------------------------------
# Fetch Outstanding Data
# ----------------------------------------
rows = get_outstanding_report(financial_year_id, start_date, end_date)

df = pd.DataFrame(rows)

if df.empty:
    st.warning("⚠️ No data found.")
    st.stop()

# Totals
total_receivable = df["Receivable (Dr)"].sum()
total_payable = df["Payable (Cr)"].sum()

st.markdown("---")
st.caption(f"From {start_date} to {end_date} (Financial Year: {active_year['label']} )")


c1, c2, c3 = st.columns(3)

c1.success(f"📥 Total Receivable\n\n₹ {total_receivable:,.2f}")
c2.error(f"📤 Total Payable\n\n₹ {total_payable:,.2f}")
c3.info(f"⚖ Net Outstanding\n\n₹ {(total_receivable - total_payable):,.2f}")

st.markdown("---")
with st.expander("## 📌 Outstanding Table", expanded=False):

    st.dataframe(df, use_container_width=True)

# ----------------------------------------
# Top 10 Receivable & Payable
# ----------------------------------------
st.markdown("---")
with st.expander("## 🔥 Top 10 Receivable Accounts", expanded=False):

    top_receivable = df.sort_values(by="Receivable (Dr)", ascending=False).head(10)
    st.dataframe(top_receivable[["Account Name", "Receivable (Dr)"]], use_container_width=True)

    st.markdown("## 🔥 Top 10 Payable Accounts")

    top_payable = df.sort_values(by="Payable (Cr)", ascending=False).head(10)
    st.dataframe(top_payable[["Account Name", "Payable (Cr)"]], use_container_width=True)

# ----------------------------------------
# Export Options
# ----------------------------------------
st.markdown("---")
with st.expander("## 📤 Export Options", expanded=False):
    colA, colB, colC = st.columns(3)

    # CSV Export
    with colA:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name=f"outstanding_{active_year['label']}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Excel Export
    with colB:
        try:
            def to_excel_v2(df_in):
                import io
                import pandas as pd

                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                    df_in.to_excel(writer, sheet_name="Outstanding", index=False)
                return output_buffer.getvalue()

            excel_data = to_excel_v2(df)

            st.download_button(
                "⬇️ Download Excel",
                data=excel_data,
                file_name=f"outstanding_{active_year['label']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Excel export failed: {e}")

    # Print HTML Export
    with colC:
        if not df.empty:
            print_html = f"""
            <html>
            <head>
                <title>Outstanding Report</title>
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
                <h2>Outstanding Report</h2>
                <p><b>Financial Year:</b> {active_year['label']}</p>
                <p><b>From:</b> {start_date} &nbsp;&nbsp; <b>To:</b> {end_date}</p>

                <p><b>Total Receivable:</b> ₹ {total_receivable:,.2f}</p>
                <p><b>Total Payable:</b> ₹ {total_payable:,.2f}</p>

                {df.to_html(index=False)}
            </body>
            </html>
            """

            st.download_button(
                "🖨 Download Print Report (HTML)",
                data=print_html.encode("utf-8"),
                file_name=f"outstanding_{active_year['label']}.html",
                mime="text/html",
                use_container_width=True
            )
