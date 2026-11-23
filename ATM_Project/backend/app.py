import os
import sqlite3
from functools import wraps
from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

from account import SavingsAccount, CurrentAccount
from atm import ATM
from database import get_connection, initialize_database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/static")
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "development-only-change-this-secret"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def api_login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "account_number" not in session:
            return jsonify({"error": "Please log in first."}), 401
        return function(*args, **kwargs)
    return wrapper


def valid_amount(value):
    try:
        amount = float(value)
        if not (amount > 0 and amount < 1_000_000_000):
            return None
        return round(amount, 2)
    except (TypeError, ValueError):
        return None


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/me")
@api_login_required
def me():
    account_number = session["account_number"]
    with get_connection() as db:
        row = db.execute("""
            SELECT account_number, holder_name, account_type, balance
            FROM accounts WHERE account_number = ?
        """, (account_number,)).fetchone()
    if row is None:
        session.clear()
        return jsonify({"error": "Account not found."}), 404
    return jsonify(dict(row))


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    account_number = str(data.get("account_number", "")).strip()
    pin = str(data.get("pin", "")).strip()

    if not account_number or not pin:
        return jsonify({"error": "Enter your account number and PIN."}), 400

    with get_connection() as db:
        row = db.execute(
            "SELECT account_number, pin_hash FROM accounts WHERE account_number = ?",
            (account_number,)
        ).fetchone()

    if row is None or not check_password_hash(row["pin_hash"], pin):
        return jsonify({"error": "Invalid account number or PIN."}), 401

    session.clear()
    session["account_number"] = account_number
    return me()


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."})


@app.get("/api/transactions")
@api_login_required
def transactions():
    account_number = session["account_number"]
    with get_connection() as db:
        rows = db.execute("""
            SELECT transaction_type, amount, created_at
            FROM transactions
            WHERE account_number = ?
            ORDER BY id DESC LIMIT 20
        """, (account_number,)).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/deposit")
@api_login_required
def deposit():
    data = request.get_json(silent=True) or {}
    amount = valid_amount(data.get("amount"))
    if amount is None:
        return jsonify({"error": "Enter a valid amount greater than zero."}), 400

    account_number = session["account_number"]
    try:
        with get_connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM accounts WHERE account_number = ?",
                (account_number,)
            ).fetchone()
            if row is None:
                raise ValueError("Account not found.")
            account_class = SavingsAccount if row["account_type"] == "savings" else CurrentAccount
            account = account_class(row["account_number"], row["holder_name"], row["balance"])
            account.deposit(amount)
            db.execute(
                "UPDATE accounts SET balance = ? WHERE account_number = ?",
                (account.balance, account_number)
            )
            ATM(account_number).record_transaction(db, "Deposit", amount)
        return jsonify({"message": "Deposit successful.", "balance": account.balance})
    except (ValueError, sqlite3.Error) as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/withdraw")
@api_login_required
def withdraw():
    data = request.get_json(silent=True) or {}
    amount = valid_amount(data.get("amount"))
    if amount is None:
        return jsonify({"error": "Enter a valid amount greater than zero."}), 400

    account_number = session["account_number"]
    try:
        with get_connection() as db:
            db.execute("BEGIN IMMEDIATE")
            atm = ATM(account_number)
            account = atm.get_account(db)
            # Polymorphic call: SavingsAccount and CurrentAccount
            # apply their own withdrawal rules.
            account.withdraw(amount)
            db.execute(
                "UPDATE accounts SET balance = ? WHERE account_number = ?",
                (account.balance, account_number)
            )
            atm.record_transaction(db, "Withdrawal", amount)
        return jsonify({"message": "Withdrawal successful.", "balance": account.balance})
    except (ValueError, sqlite3.Error) as error:
        return jsonify({"error": str(error)}), 400


@app.post("/api/change-pin")
@api_login_required
def change_pin():
    data = request.get_json(silent=True) or {}
    old_pin = str(data.get("old_pin", "")).strip()
    new_pin = str(data.get("new_pin", "")).strip()

    if len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"error": "New PIN must contain exactly 4 digits."}), 400

    account_number = session["account_number"]
    with get_connection() as db:
        row = db.execute(
            "SELECT pin_hash FROM accounts WHERE account_number = ?",
            (account_number,)
        ).fetchone()
        if row is None or not check_password_hash(row["pin_hash"], old_pin):
            return jsonify({"error": "Current PIN is incorrect."}), 401
        db.execute(
            "UPDATE accounts SET pin_hash = ? WHERE account_number = ?",
            (generate_password_hash(new_pin), account_number)
        )
    return jsonify({"message": "PIN changed successfully."})


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "API endpoint not found."}), 404
    return "Page not found", 404


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, port=5000)
