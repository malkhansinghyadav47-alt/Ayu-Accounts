import re
import sqlite3
import pandas as pd
from datetime import date
from datetime import datetime

DB_NAME = "business_ledger.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# -------------------------------
# Financial Year Helpers
# -------------------------------

def get_active_financial_year():
    conn = get_connection()
    cur = conn.cursor()
    # 1. Fetch all needed columns
    cur.execute("SELECT id, label, start_date, end_date FROM financial_years WHERE is_active = 1")
    row = cur.fetchone()
    conn.close()

    if row:
        # 2. Return a dictionary so the calling code works
        return {
            "id": row[0],
            "label": row[1],
            "start_date": row[2],
            "end_date": row[3]
        }
    else:
        # 3. Return None instead of a string for cleaner logic
        return None

def get_all_financial_years():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, label, start_date, end_date, is_active
            FROM financial_years
            ORDER BY start_date DESC
        """)
        return cur.fetchall()


def set_active_financial_year(year_id):
    with get_connection() as conn:
        cur = conn.cursor()

        # deactivate all
        cur.execute("UPDATE financial_years SET is_active = 0")

        # activate selected
        cur.execute("""
            UPDATE financial_years 
            SET is_active = 1 
            WHERE id = ?
        """, (year_id,))

        conn.commit()
        
# -------------------------------
# Financial Year CRUD Helpers
# -------------------------------

def generate_fy_dates(label):
    """
    Converts '2026-27' → ('2026-04-01', '2027-03-31')
    Enforces:
    - Format YYYY-YY
    - Year between 2000 and 2099
    """

    pattern = r"^(\d{4})-(\d{2})$"
    match = re.match(pattern, label.strip())

    if not match:
        raise ValueError("Invalid format. Use YYYY-YY (e.g. 2026-27)")

    start_year = int(match.group(1))
    end_year_suffix = int(match.group(2))

    # 🔒 Century bound check
    if start_year < 2000 or start_year > 2099:
        raise ValueError("Financial year must be between 2000-01 and 2099-00")

    # 🔒 Logical FY continuity check
    if (start_year + 1) % 100 != end_year_suffix:
        raise ValueError("Invalid financial year sequence (e.g. 2026-27)")

    start_date = date(start_year, 4, 1)
    end_date = date(start_year + 1, 3, 31)

    return start_date.isoformat(), end_date.isoformat()

def add_financial_year(label):
    try:
        start_date, end_date = generate_fy_dates(label)

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO financial_years (label, start_date, end_date, is_active)
                VALUES (?, ?, ?, 0)
            """, (label.strip(), start_date, end_date))
            conn.commit()

        return True, ""

    except ValueError as ve:
        return False, str(ve)

    except sqlite3.IntegrityError:
        return False, f"Financial Year '{label}' already exists"


def update_financial_year(year_id, label):

    label = label.strip()
    start_date, end_date = generate_fy_dates(label)

    with get_connection() as conn:
        cur = conn.cursor()

        # 🔒 Check duplicate label EXCEPT current record
        cur.execute("""
            SELECT id 
            FROM financial_years 
            WHERE label = ? AND id != ?
        """, (label, year_id))

        if cur.fetchone():
            raise ValueError(f"Financial Year '{label}' already exists")

        # ✅ Safe update
        cur.execute("""
            UPDATE financial_years
            SET label = ?, start_date = ?, end_date = ?
            WHERE id = ?
        """, (label, start_date, end_date, year_id))

        conn.commit()

def can_delete_financial_year(year_id):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM opening_balances WHERE financial_year_id = ?",
            (year_id,)
        )
        if cur.fetchone()[0] > 0:
            return False

        cur.execute(
            "SELECT COUNT(*) FROM transactions WHERE financial_year_id = ?",
            (year_id,)
        )
        if cur.fetchone()[0] > 0:
            return False

        return True

def delete_financial_year(year_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM financial_years WHERE id = ?", (year_id,))
        conn.commit()
        
# -------------------------------
# Groups Helpers
# -------------------------------

def add_group(group_name):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO groups (group_name) VALUES (?)",
            (group_name.strip(),)
        )
        conn.commit()

def get_all_groups():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, group_name FROM groups ORDER BY group_name")
        return cur.fetchall()

def update_group(group_id, new_name):
    new_name = new_name.strip()

    if not new_name:
        raise ValueError("Group name cannot be empty")

    with get_connection() as conn:
        cur = conn.cursor()

        # Duplicate check
        cur.execute("""
            SELECT id FROM groups
            WHERE group_name = ? AND id != ?
        """, (new_name, group_id))

        if cur.fetchone():
            raise ValueError("Group already exists")

        cur.execute("""
            UPDATE groups
            SET group_name = ?
            WHERE id = ?
        """, (new_name, group_id))

        conn.commit()

def can_delete_group(group_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM accounts WHERE group_id = ?",
            (group_id,)
        )
        return cur.fetchone()[0] == 0

def delete_group(group_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()


# -------------------------------
# ACCOUNTS HELPERS
# -------------------------------

import sqlite3

def get_all_groups():
    with get_connection() as conn:
        # This ensures row['column'] works, but we'll go one step further
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT id, group_name FROM groups ORDER BY group_name")
        rows = cur.fetchall()
        # Convert to true dictionaries so .get() works in Streamlit
        return [dict(row) for row in rows]

def get_all_accounts():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                a.id, a.name, a.phone, a.address, 
                a.is_active, a.group_id, g.group_name
            FROM accounts a
            JOIN groups g ON a.group_id = g.id
            ORDER BY a.name
        """)
        rows = cur.fetchall()
        return [dict(row) for row in rows]

def add_account(name, group_id, phone="", address=""):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (name, group_id, phone, address)
            VALUES (?, ?, ?, ?)
        """, (name.strip(), group_id, phone.strip(), address.strip()))
        conn.commit()

def update_account(account_id, name, group_id, phone="", address=""):
    name = name.strip()
    if not name:
        raise ValueError("Account name cannot be empty")
    if group_id is None:
        raise ValueError("Group ID is required")

    with get_connection() as conn:
        cur = conn.cursor()

        # Check for duplicate names
        cur.execute("""
            SELECT id FROM accounts
            WHERE name = ? AND id != ?
        """, (name, account_id))

        if cur.fetchone():
            raise ValueError("Account name already exists")

        # Match the order of parameters to the SET clause
        cur.execute("""
            UPDATE accounts
            SET name = ?, group_id = ?, phone = ?, address = ?
            WHERE id = ?
        """, (name, group_id, phone, address, account_id))

        conn.commit()

def deactivate_account(account_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE accounts
            SET is_active = 0
            WHERE id = ?
        """, (account_id,))
        conn.commit()

def get_groups_for_dropdown():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, group_name FROM groups ORDER BY group_name")
        return cur.fetchall()

def toggle_account_status(account_id, is_active):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE accounts
        SET is_active = ?
        WHERE id = ?
    """, (is_active, account_id))

    conn.commit()
    conn.close()
        
def can_delete_account(account_id):
    """Checks if the account is linked to any transactions or opening balances."""
    with get_connection() as conn:
        cur = conn.cursor()
        # Check Transactions
        cur.execute("SELECT COUNT(*) FROM transactions WHERE from_acc_id = ? OR to_acc_id = ?", (account_id, account_id))
        if cur.fetchone()[0] > 0: return False
        
        # Check Opening Balances (assuming you have an opening_balances table)
        cur.execute("SELECT COUNT(*) FROM opening_balances WHERE account_id = ?", (account_id,))
        if cur.fetchone()[0] > 0: return False
        
    return True

def delete_account(account_id):
    """Permanently removes an account."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()

       
# -------------------------------
# OPENING BALANCE HELPERS
# -------------------------------

def get_all_accounts_simple():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM accounts WHERE is_active = 1 ORDER BY name")
        return cur.fetchall()


def add_opening_balance(account_id, financial_year_id, amount):
    if has_transactions(account_id, financial_year_id):
        raise ValueError("Opening balance locked (transactions exist)")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO opening_balances
            (account_id, financial_year_id, amount)
            VALUES (?, ?, ?)
        """, (account_id, financial_year_id, amount))
        conn.commit()

# gete multiple opening balances
def get_opening_balances(financial_year_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.name, ob.amount
            FROM opening_balances ob
            JOIN accounts a ON ob.account_id = a.id
            WHERE ob.financial_year_id = ?
            ORDER BY a.name
        """, (financial_year_id,))
        return cur.fetchall()

def has_transactions(account_id, financial_year_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE financial_year_id = ?
              AND (from_acc_id = ? OR to_acc_id = ?)
        """, (financial_year_id, account_id, account_id))
        return cur.fetchone()[0] > 0

# get single account opening balance
def get_opening_balance(account_id, financial_year_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT amount
            FROM opening_balances
            WHERE account_id = ?
              AND financial_year_id = ?
        """, (account_id, financial_year_id))

        row = cur.fetchone()
        return float(row["amount"]) if row and row["amount"] is not None else 0.0

# ---------------------------------
# TRANSACTIONS HELPERS
# ---------------------------------

def add_transaction(
    txn_date,
    from_acc_id,
    to_acc_id,
    amount,
    note,
    financial_year_id,
    created_by=1   # 👈 default
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions 
        (txn_date, from_acc_id, to_acc_id, amount, note, financial_year_id, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        txn_date,
        from_acc_id,
        to_acc_id,
        amount,
        note,
        financial_year_id,
        created_by,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

def get_transactions_by_year(financial_year_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            t.id,
            t.txn_date,
            a1.name AS from_account,
            a2.name AS to_account,
            t.amount,
            t.note
        FROM transactions t
        JOIN accounts a1 ON t.from_acc_id = a1.id
        JOIN accounts a2 ON t.to_acc_id = a2.id
        WHERE t.financial_year_id = ?
        ORDER BY t.txn_date DESC, t.id DESC
    """, (financial_year_id,))

    rows = cur.fetchall()
    conn.close()
    return rows

def get_transaction_summary(financial_year_id):
    """Returns total Debit, Credit and Entry Count for a financial year"""
    with get_connection() as conn:
        cur = conn.cursor()

        # Total Debit
        cur.execute("""
            SELECT SUM(amount)
            FROM transactions
            WHERE financial_year_id = ?
        """, (financial_year_id,))
        total_debit = cur.fetchone()[0] or 0.0

        # Total Credit (same total in double-entry, but kept explicit)
        cur.execute("""
            SELECT SUM(amount)
            FROM transactions
            WHERE financial_year_id = ?
        """, (financial_year_id,))
        total_credit = cur.fetchone()[0] or 0.0

        # Entry count
        cur.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE financial_year_id = ?
        """, (financial_year_id,))
        entry_count = cur.fetchone()[0] or 0

        return {
            "debit": total_debit,
            "credit": total_credit,
            "entries": entry_count
        }

def delete_transaction(txn_id):
    """Removes a transaction from the database."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()

def update_transaction(txn_id, amount, note, from_acc_id, to_acc_id):
    """Updates the amount, note, and accounts of an existing transaction."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE transactions 
            SET amount = ?, note = ?, from_acc_id = ?, to_acc_id = ?
            WHERE id = ?
        """, (amount, note, from_acc_id, to_acc_id, txn_id))
        conn.commit()
  
def get_account_dr_cr(account_id, financial_year_id):
    """Returns Debit and Credit total for a single account"""
    with get_connection() as conn:
        cur = conn.cursor()

        # Debit
        cur.execute("""
            SELECT SUM(amount)
            FROM transactions
            WHERE to_acc_id = ?
              AND financial_year_id = ?
        """, (account_id, financial_year_id))
        debit = cur.fetchone()[0] or 0.0

        # Credit
        cur.execute("""
            SELECT SUM(amount)
            FROM transactions
            WHERE from_acc_id = ?
              AND financial_year_id = ?
        """, (account_id, financial_year_id))
        credit = cur.fetchone()[0] or 0.0

        return debit, credit
  
            
# -------------------------------
# Date Helpers
# ------------------------------

def indian_date(date_str):
    # DB format YYYY-MM-DD  →  DD-MM-YYYY
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")


# -------------------------------
# Reports Helpers
# ------------------------------

def get_ledger(account_id, financial_year_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                txn_date,
                note,
                CASE 
                    WHEN to_acc_id = ? THEN amount
                    ELSE 0
                END AS debit,
                CASE 
                    WHEN from_acc_id = ? THEN amount
                    ELSE 0
                END AS credit
            FROM transactions
            WHERE financial_year_id = ?
              AND (from_acc_id = ? OR to_acc_id = ?)
            ORDER BY txn_date, id
        """, (account_id, account_id, financial_year_id, account_id, account_id))
        return cur.fetchall()
  
def get_account_ledger(account_id, financial_year_id, start_date=None, end_date=None):
    """
    Returns ledger rows for a given account_id including Dr/Cr effect.
    Output columns:
        txn_date, particular, debit, credit, note
    """

    with get_connection() as conn:
        cur = conn.cursor()

        query = """
            SELECT 
                t.txn_date AS txn_date,
                a2.name AS particular,
                t.amount AS debit,
                0 AS credit,
                t.note AS note
            FROM transactions t
            JOIN accounts a2 ON t.from_acc_id = a2.id
            WHERE t.to_acc_id = ?
              AND t.financial_year_id = ?

            UNION ALL

            SELECT 
                t.txn_date AS txn_date,
                a1.name AS particular,
                0 AS debit,
                t.amount AS credit,
                t.note AS note
            FROM transactions t
            JOIN accounts a1 ON t.to_acc_id = a1.id
            WHERE t.from_acc_id = ?
              AND t.financial_year_id = ?
        """

        params = [account_id, financial_year_id, account_id, financial_year_id]

        # Date Filter if provided
        if start_date and end_date:
            query = f"""
                SELECT * FROM ({query})
                WHERE txn_date BETWEEN ? AND ?
                ORDER BY txn_date ASC
            """
            params.extend([start_date, end_date])
        else:
            query = f"""
                SELECT * FROM ({query})
                ORDER BY txn_date ASC
            """

        cur.execute(query, params)
        rows = cur.fetchall()

        return rows

def calculate_running_ledger(ledger_rows, opening_balance):
    """
    ledger_rows = list of tuples (txn_date, particular, debit, credit, note)
    returns list with running balance.
    """

    running = opening_balance
    output = []

    total_dr = 0
    total_cr = 0

    for row in ledger_rows:
        txn_date, particular, debit, credit, note = row

        debit = debit or 0
        credit = credit or 0

        total_dr += debit
        total_cr += credit

        running = running + debit - credit

        # Balance side
        if running >= 0:
            bal_side = "Dr"
            bal_amt = running
        else:
            bal_side = "Cr"
            bal_amt = abs(running)

        output.append({
            "Date": txn_date,
            "Particular": particular,
            "Debit": debit,
            "Credit": credit,
            "Note": note,
            "Balance": f"{bal_amt:.2f} {bal_side}"
        })

    closing_balance = running

    return output, total_dr, total_cr, closing_balance

# -----------------------------------------
# Helper: Get Account Closing Balance
# -----------------------------------------
def get_account_closing_balance(account_id, financial_year_id, start_date, end_date):
    """
    Closing Balance = Opening + Debit(to_acc) - Credit(from_acc)
    Opening is already signed (+ debit, - credit)
    """

    conn = get_connection()
    cursor = conn.cursor()

    # Opening Balance
    cursor.execute("""
        SELECT COALESCE(amount, 0)
        FROM opening_balances
        WHERE account_id = ? AND financial_year_id = ?
    """, (account_id, financial_year_id))

    opening = cursor.fetchone()
    opening_amt = opening[0] if opening else 0.0

    # Total Debit (Received)
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE to_acc_id = ?
          AND financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
    """, (account_id, financial_year_id, start_date, end_date))

    total_dr = cursor.fetchone()[0]

    # Total Credit (Paid)
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE from_acc_id = ?
          AND financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
    """, (account_id, financial_year_id, start_date, end_date))

    total_cr = cursor.fetchone()[0]

    conn.close()

    closing = opening_amt + total_dr - total_cr
    return closing

def get_all_balances_optimized(financial_year_id, start_date, end_date):
    """
    Optimized: Fetches all account balances in one query using CTEs.
    Matches your logic: Opening + Debits (to_acc_id) - Credits (from_acc_id)
    """
    conn = get_connection()
    
    query = """
    WITH Opening AS (
        SELECT account_id, COALESCE(amount, 0) as op_amt 
        FROM opening_balances 
        WHERE financial_year_id = ?
    ),
    Debits AS (
        SELECT to_acc_id as account_id, SUM(amount) as dr_amt 
        FROM transactions 
        WHERE financial_year_id = ? AND txn_date BETWEEN ? AND ?
        GROUP BY to_acc_id
    ),
    Credits AS (
        SELECT from_acc_id as account_id, SUM(amount) as cr_amt 
        FROM transactions 
        WHERE financial_year_id = ? AND txn_date BETWEEN ? AND ?
        GROUP BY from_acc_id
    )
    SELECT 
        a.id as acc_id, 
        a.name as acc_name, 
        a.group_id,
        g.group_name,
        (COALESCE(o.op_amt, 0) + COALESCE(d.dr_amt, 0) - COALESCE(c.cr_amt, 0)) as balance
    FROM accounts a
    JOIN groups g ON a.group_id = g.id
    LEFT JOIN Opening o ON a.id = o.account_id
    LEFT JOIN Debits d ON a.id = d.account_id
    LEFT JOIN Credits c ON a.id = c.account_id
    """
    
    params = (
        financial_year_id, 
        financial_year_id, start_date, end_date, 
        financial_year_id, start_date, end_date
    )
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# -----------------------------------------
# Helper: Format Amount
# -----------------------------------------
def format_amt(val):
    return f"₹ {val:,.2f}"

    
def generate_voucher_no(voucher_type_id, financial_year_id):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT COALESCE(MAX(voucher_seq), 0)
            FROM transactions
            WHERE financial_year_id = ?
              AND voucher_type_id = ?
        """, (financial_year_id, voucher_type_id))

        next_seq = cur.fetchone()[0] + 1

        voucher_no = f"{voucher_type_id}/{financial_year_id}/{next_seq:05d}"
        return voucher_no, next_seq


# -----------------------------------------
# CASH FLOW REPORT FUNCTIONS
# -----------------------------------------

def get_cash_bank_accounts(financial_year_id):
    """
    Returns list of accounts which belong to CASH/BANK group ids.
    NOTE: You must define your CASH/BANK group ids properly.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # 👇 यहां group_id numbers वही डालो जो आपकी DB में CASH/BANK group के हैं
    CASH_BANK_GROUP_IDS = (1, 2)   # <-- Change this as per your group ids

    cursor.execute(f"""
        SELECT id, name
        FROM accounts
        WHERE group_id IN ({",".join(["?"]*len(CASH_BANK_GROUP_IDS))})
        ORDER BY name
    """, CASH_BANK_GROUP_IDS)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_opening_balance(account_id, financial_year_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(amount, 0)
        FROM opening_balances
        WHERE account_id = ?
          AND financial_year_id = ?
    """, (account_id, financial_year_id))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0


def get_cash_flow_summary(account_id, financial_year_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    # Cash In
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
          AND to_acc_id = ?
    """, (financial_year_id, start_date, end_date, account_id))
    cash_in = cursor.fetchone()[0]

    # Cash Out
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
          AND from_acc_id = ?
    """, (financial_year_id, start_date, end_date, account_id))
    cash_out = cursor.fetchone()[0]

    conn.close()

    return {
        "cash_in": cash_in,
        "cash_out": cash_out,
        "net_cash_flow": cash_in - cash_out
    }

def get_cash_flow_transactions(account_id, financial_year_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            t.id,
            t.txn_date,
            t.note,
            a1.name AS from_account,
            a2.name AS to_account,
            t.from_acc_id,
            t.to_acc_id,
            t.amount
        FROM transactions t
        LEFT JOIN accounts a1 ON a1.id = t.from_acc_id
        LEFT JOIN accounts a2 ON a2.id = t.to_acc_id
        WHERE t.financial_year_id = ?
          AND t.txn_date BETWEEN ? AND ?
          AND (t.from_acc_id = ? OR t.to_acc_id = ?)
        ORDER BY t.txn_date ASC, t.id ASC
    """, (financial_year_id, start_date, end_date, account_id, account_id))

    rows = cursor.fetchall()
    conn.close()

    return rows

def get_cash_closing_balance(account_id, financial_year_id, start_date, end_date):
    opening = get_opening_balance(account_id, financial_year_id)
    summary = get_cash_flow_summary(account_id, financial_year_id, start_date, end_date)
    return opening + summary["net_cash_flow"]

def get_day_book_transactions(financial_year_id, start_date, end_date):
    """
    Returns all transactions in date range for Day Book.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.id,
            t.txn_date,
            COALESCE(t.note, ''),
            t.amount,
            t.from_acc_id,
            fa.name AS from_account,
            t.to_acc_id,
            ta.name AS to_account
        FROM transactions t
        LEFT JOIN accounts fa ON fa.id = t.from_acc_id
        LEFT JOIN accounts ta ON ta.id = t.to_acc_id
        WHERE t.financial_year_id = ?
          AND t.txn_date BETWEEN ? AND ?
        ORDER BY t.txn_date ASC, t.id ASC
    """, (financial_year_id, start_date, end_date))

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_day_book_summary(financial_year_id, start_date, end_date):
    """
    Returns total debit/credit counts and total amount summary.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
    """, (financial_year_id, start_date, end_date))

    total_amount = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
    """, (financial_year_id, start_date, end_date))

    total_entries = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_amount": float(total_amount),
        "total_entries": int(total_entries)
    }

def get_account_closing_balance(account_id, financial_year_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    # Opening Balance
    cursor.execute("""
        SELECT COALESCE(amount, 0)
        FROM opening_balances
        WHERE account_id = ? AND financial_year_id = ?
    """, (account_id, financial_year_id))

    opening = cursor.fetchone()
    opening_balance = float(opening[0]) if opening else 0.0

    # Transactions Impact
    cursor.execute("""
        SELECT 
            COALESCE(SUM(
                CASE 
                    WHEN to_acc_id = ? THEN amount
                    WHEN from_acc_id = ? THEN -amount
                    ELSE 0
                END
            ), 0)
        FROM transactions
        WHERE financial_year_id = ?
          AND txn_date BETWEEN ? AND ?
    """, (account_id, account_id, financial_year_id, start_date, end_date))

    txn_sum = cursor.fetchone()[0] or 0.0

    conn.close()

    return opening_balance + float(txn_sum)

def get_outstanding_report(financial_year_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, group_id
        FROM accounts
        ORDER BY name
    """)
    accounts = cursor.fetchall()

    result = []

    for acc in accounts:
        acc_id = acc[0]
        acc_name = acc[1]

        closing = get_account_closing_balance(acc_id, financial_year_id, start_date, end_date)

        dr_amt = 0.0
        cr_amt = 0.0

        if closing > 0:
            dr_amt = closing
        elif closing < 0:
            cr_amt = abs(closing)

        result.append({
            "Account ID": acc_id,
            "Account Name": acc_name,
            "Receivable (Dr)": round(dr_amt, 2),
            "Payable (Cr)": round(cr_amt, 2),
            "Net Balance": round(closing, 2)
        })

    conn.close()
    return result

def get_groupwise_outstanding(financial_year_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all groups
    cursor.execute("""
        SELECT id, group_name
        FROM groups
        ORDER BY group_name
    """)
    groups = cursor.fetchall()

    result = []

    for g in groups:
        group_id = g[0]
        group_name = g[1]

        # Accounts under this group
        cursor.execute("""
            SELECT id, name
            FROM accounts
            WHERE group_id = ?
        """, (group_id,))
        accounts = cursor.fetchall()

        total_receivable = 0.0
        total_payable = 0.0
        net_balance = 0.0

        for acc in accounts:
            acc_id = acc[0]

            closing = get_account_closing_balance(acc_id, financial_year_id, start_date, end_date)

            net_balance += closing

            if closing > 0:
                total_receivable += closing
            elif closing < 0:
                total_payable += abs(closing)

        # Only show groups which have outstanding
        if total_receivable > 0 or total_payable > 0:
            result.append({
                "Group ID": group_id,
                "Group Name": group_name,
                "Receivable (Dr)": round(total_receivable, 2),
                "Payable (Cr)": round(total_payable, 2),
                "Net Balance": round(net_balance, 2)
            })

    conn.close()
    return result

def get_group_outstanding_accounts(group_id, financial_year_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM accounts
        WHERE group_id = ?
        ORDER BY name
    """, (group_id,))

    accounts = cursor.fetchall()

    result = []

    for acc in accounts:
        acc_id = acc[0]
        acc_name = acc[1]

        closing = get_account_closing_balance(acc_id, financial_year_id, start_date, end_date)

        dr_amt = 0.0
        cr_amt = 0.0

        if closing > 0:
            dr_amt = closing
        elif closing < 0:
            cr_amt = abs(closing)

        if dr_amt > 0 or cr_amt > 0:
            result.append({
                "Account ID": acc_id,
                "Account Name": acc_name,
                "Receivable (Dr)": round(dr_amt, 2),
                "Payable (Cr)": round(cr_amt, 2),
                "Net Balance": round(closing, 2)
            })

    conn.close()
    return result

def get_accounts_list(financial_year_id, mode="ALL"):
    """
    mode = "ALL"   => All accounts alphabetical
    mode = "GROUP" => Group-wise alphabetical + account alphabetical
    """

    with get_connection() as conn:
        cur = conn.cursor()

        if mode == "ALL":
            cur.execute("""
                SELECT 
                    a.id,
                    a.name,
                    g.group_name,
                    COALESCE(ob.amount, 0) AS opening_amount
                FROM accounts a
                LEFT JOIN groups g ON a.group_id = g.id
                LEFT JOIN opening_balances ob 
                    ON ob.account_id = a.id AND ob.financial_year_id = ?
                ORDER BY a.name
            """, (financial_year_id,))

        else:  # mode == "GROUP"
            cur.execute("""
                SELECT 
                    a.id,
                    a.name,
                    g.group_name,
                    COALESCE(ob.amount, 0) AS opening_amount
                FROM accounts a
                LEFT JOIN groups g ON a.group_id = g.id
                LEFT JOIN opening_balances ob 
                    ON ob.account_id = a.id AND ob.financial_year_id = ?
                ORDER BY g.group_name, a.name
            """, (financial_year_id,))

        return cur.fetchall()

def get_group_summary_opening(financial_year_id):
    """
    Returns group-wise opening balance summary.
    Shows total opening amount per group.
    """

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                g.group_name,
                SUM(COALESCE(ob.amount, 0)) AS total_opening
            FROM accounts a
            LEFT JOIN groups g ON a.group_id = g.id
            LEFT JOIN opening_balances ob
                ON ob.account_id = a.id AND ob.financial_year_id = ?
            GROUP BY g.group_name
            ORDER BY g.group_name
        """, (financial_year_id,))

        return cur.fetchall()


# ------------------ TOTAL INCOME ------------------

def get_total_income():
    conn = get_connection()
    fy = get_active_financial_year()

    if not fy:
        return 0

    fy_id = fy["id"]

    query = """
    SELECT SUM(t.amount)
    FROM transactions t
    JOIN accounts a ON t.to_acc_id = a.id
    JOIN groups g ON a.group_id = g.id
    WHERE g.group_name LIKE '%Income%'
    AND t.financial_year_id = ?
    """

    result = conn.execute(query, (fy_id,)).fetchone()
    conn.close()
    return result[0] if result and result[0] else 0 

# ------------------ TOTAL EXPENSE ------------------

def get_total_expense():
    conn = get_connection()
    fy = get_active_financial_year()
    if not fy:
        return 0

    fy_id = fy["id"]
    
    query = """
    SELECT SUM(t.amount)
    FROM transactions t
    JOIN accounts a ON t.from_acc_id = a.id
    JOIN groups g ON a.group_id = g.id
    WHERE g.group_name LIKE '%Expense%'
    AND t.financial_year_id = ?
    """

    row = conn.execute(query, (fy_id,)).fetchone()
    conn.close()
    return row[0] if row and row[0] else 0


# ------------------ CASH BALANCE ------------------

def get_cash_balance():
    conn = get_connection()
    fy = get_active_financial_year()
    if not fy:
        return 0

    fy_id = fy["id"]
    
    query = """
    SELECT 
        SUM(CASE WHEN a.name = 'Cash' THEN t.amount ELSE 0 END) -
        SUM(CASE WHEN b.name = 'Cash' THEN -t.amount ELSE 0 END)
    FROM transactions t
    JOIN accounts a ON t.to_acc_id = a.id
    JOIN accounts b ON t.from_acc_id = b.id
    WHERE t.financial_year_id = ?
    """

    result = conn.execute(query, (fy_id,)).fetchone()[0]
    conn.close()
    return result or 0


# ------------------ RECEIVABLE ------------------

def get_receivable():
    conn = get_connection()
    fy = get_active_financial_year()
    if not fy:
        return 0

    fy_id = fy["id"]
    
    query = """
    SELECT SUM(t.amount)
    FROM transactions t
    JOIN accounts a ON t.to_acc_id = a.id
    JOIN groups g ON a.group_id = g.id
    WHERE g.group_name LIKE '%Debtor%'
    AND t.financial_year_id = ?
    """

    result = conn.execute(query, (fy_id,)).fetchone()[0]
    conn.close()
    return result or 0


# ------------------ PAYABLE ------------------

def get_payable():
    conn = get_connection()
    fy = get_active_financial_year()
    if not fy:
        return 0

    fy_id = fy["id"]
    
    query = """
    SELECT SUM(t.amount)
    FROM transactions t
    JOIN accounts a ON t.from_acc_id = a.id
    JOIN groups g ON a.group_id = g.id
    WHERE g.group_name LIKE '%Creditor%'
    AND t.financial_year_id = ?
    """

    result = conn.execute(query, (fy_id,)).fetchone()[0]
    conn.close()
    return result or 0


# ------------------ MONTHLY DATA ------------------

def get_monthly_income_expense():
    conn = get_connection()
    fy = get_active_financial_year()
    if not fy:
        return pd.DataFrame()

    fy_id = fy["id"]

    query = """
    SELECT 
        strftime('%m', t.txn_date) as month,

        SUM(CASE 
            WHEN g1.group_name LIKE '%Income%' 
            THEN t.amount ELSE 0 END) as income,

        SUM(CASE 
            WHEN g2.group_name LIKE '%Expense%' 
            THEN t.amount ELSE 0 END) as expense

    FROM transactions t

    LEFT JOIN accounts a1 ON t.to_acc_id = a1.id
    LEFT JOIN groups g1 ON a1.group_id = g1.id

    LEFT JOIN accounts a2 ON t.from_acc_id = a2.id
    LEFT JOIN groups g2 ON a2.group_id = g2.id

    WHERE t.financial_year_id = ?
    GROUP BY month
    ORDER BY month
    """

    df = pd.read_sql(query, conn, params=(fy_id,))
    conn.close()
    return df
