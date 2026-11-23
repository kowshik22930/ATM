import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).with_name("atm.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_number TEXT PRIMARY KEY,
                holder_name TEXT NOT NULL,
                pin_hash TEXT NOT NULL,
                account_type TEXT NOT NULL CHECK(account_type IN ('savings', 'current')),
                balance REAL NOT NULL CHECK(balance >= 0)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_number) REFERENCES accounts(account_number)
            )
        """)

        # Demo account is inserted only if it does not already exist.
        existing = db.execute(
            "SELECT account_number FROM accounts WHERE account_number = ?",
            ("1001",)
        ).fetchone()
        if existing is None:
            db.execute("""
                INSERT INTO accounts
                (account_number, holder_name, pin_hash, account_type, balance)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "1001", "Demo User", generate_password_hash("1234"),
                "savings", 10000.00
            ))
