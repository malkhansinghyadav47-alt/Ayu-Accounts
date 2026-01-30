import sqlite3

def init_db():
    with sqlite3.connect("business_ledger.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1. Account Groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL
            )
        """)

        # 2. Financial Years
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT UNIQUE NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active INTEGER DEFAULT 0
            )
        """)
        
        # 3. Users Roles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                role_name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)
        
        # Seed Roles
        roles = [
            (1, 'SUPERADMIN', 'Full system access'),
            (2, 'ADMIN', 'Manage accounts and entries'),
            (3, 'USER', 'View-only or limited entry')
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO roles (id, role_name, description)
            VALUES (?, ?, ?)
        """, roles)

        # 3. Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT,
                role_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """)

        # 3. Accounts Master
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                address TEXT,
                group_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        """)

        # 4. Opening Balances
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opening_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                financial_year_id INTEGER NOT NULL,
                amount REAL NOT NULL, -- (+ Debit / - Credit)
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (financial_year_id) REFERENCES financial_years(id),
                UNIQUE (account_id, financial_year_id)
            )
        """)

        # 5. Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_date DATE NOT NULL,
                from_acc_id INTEGER NOT NULL,
                to_acc_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                note TEXT,
                financial_year_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (from_acc_id) REFERENCES accounts(id),
                FOREIGN KEY (to_acc_id) REFERENCES accounts(id),
                FOREIGN KEY (financial_year_id) REFERENCES financial_years(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # 6. Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(txn_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_fy ON transactions(financial_year_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opening_fy ON opening_balances(financial_year_id)")

        # 7. Seed Data: Groups
        groups = ['Assets', 'Liabilities', 'Income', 'Expenses', 'Equity']
        cursor.executemany("INSERT OR IGNORE INTO groups (group_name) VALUES (?)", [(g,) for g in groups])

        # 8. Seed Data: Financial Years
        # (Updated to ensure 2025-26 is marked active during initial creation)
        years = [2023, 2024, 2025, 2026]
        for y in years:
            label = f"{y}-{str(y+1)[-2:]}"
            active_status = 1 if label == '2026-27' else 0
            cursor.execute("""
                INSERT OR IGNORE INTO financial_years (label, start_date, end_date, is_active)
                VALUES (?, ?, ?, ?)
            """, (label, f"{y}-04-01", f"{y+1}-03-31", active_status))

        # 10. Seed Default User (ADMIN)
        cursor.execute("""
            INSERT OR IGNORE INTO users (id, username, full_name, role_id)
            VALUES (1, 'admin', 'System Administrator', 1)
        """)

        # 9. Seed Data: Default Accounts
        default_accounts = [
            ('Cash', 'Assets'),
            ('Bank', 'Assets'),
            ('Sales Income', 'Income'),
            ('Office Expenses', 'Expenses'),
            ('Salary Expense', 'Expenses'),
            ('Opening Balance Equity', 'Equity')
        ]

        for acc_name, grp_name in default_accounts:
            # Safer fetch: ensures the group exists before trying to insert the account
            cursor.execute("SELECT id FROM groups WHERE group_name = ?", (grp_name,))
            row = cursor.fetchone()
            if row:
                grp_id = row[0]
                cursor.execute("""
                    INSERT OR IGNORE INTO accounts (name, group_id)
                    VALUES (?, ?)
                """, (acc_name, grp_id))

        conn.commit()
        print("✅ Professional Accounting Database Initialized Successfully.")

if __name__ == "__main__":
    init_db()