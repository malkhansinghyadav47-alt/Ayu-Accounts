import sqlite3
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


# -------------------------------
# ACCOUNTS HELPERS
# -------------------------------

def get_all_accounts():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.name, a.phone, a.address, a.is_active, g.group_name
            FROM accounts a
            JOIN groups g ON a.group_id = g.id
            ORDER BY a.name
        """)
        return cur.fetchall()


def add_account(name, group_id, phone="", address=""):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (name, group_id, phone, address)
            VALUES (?, ?, ?, ?)
        """, (name.strip(), group_id, phone.strip(), address.strip()))
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
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO opening_balances 
            (account_id, financial_year_id, amount)
            VALUES (?, ?, ?)
        """, (account_id, financial_year_id, amount))
        conn.commit()


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


# ---------------------------------
# TRANSACTIONS HELPERS
# ---------------------------------

def add_transaction(txn_date, from_acc_id, to_acc_id, amount, note, financial_year_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions 
        (txn_date, from_acc_id, to_acc_id, amount, note, financial_year_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (txn_date, from_acc_id, to_acc_id, amount, note, financial_year_id))

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

# -------------------------------
# Date Helpers
# ------------------------------

def indian_date(date_str):
    # DB format YYYY-MM-DD  →  DD-MM-YYYY
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")

