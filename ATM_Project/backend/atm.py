from account import SavingsAccount, CurrentAccount


class ATM:
    def __init__(self, account_number):
        self.account_number = account_number

    def get_account(self, db):
        row = db.execute(
            "SELECT * FROM accounts WHERE account_number = ?",
            (self.account_number,)
        ).fetchone()

        if row is None:
            raise ValueError("Account not found.")

        account_class = (
            SavingsAccount if row["account_type"] == "savings"
            else CurrentAccount
        )
        # Polymorphism: ATM calls withdraw() without needing to know
        # which concrete account class is being used.
        account = account_class(
            row["account_number"], row["holder_name"], row["balance"]
        )
        return account

    def record_transaction(self, db, transaction_type, amount):
        db.execute("""
            INSERT INTO transactions (account_number, transaction_type, amount)
            VALUES (?, ?, ?)
        """, (self.account_number, transaction_type, amount))
