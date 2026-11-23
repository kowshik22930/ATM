# ATM Simulation — Python OOP + Flask

A learning project demonstrating Python OOP concepts with a Flask API, SQLite database, and HTML/CSS/JavaScript frontend.

## Requirements
- Python 3.9+
- pip

## Run on Windows (VS Code terminal)

1. Open the `ATM_Project` folder in VS Code.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```powershell
   pip install -r backend/requirements.txt
   ```

4. Start the Flask app:

   ```powershell
   cd backend
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.

## Demo credentials
- Account number: `1001`
- PIN: `1234`
- Initial balance: ₹10,000
- Account type: Savings

The demo account is created automatically the first time the app starts. Its data is stored in `backend/atm.db`.

## OOP concepts
- **Encapsulation:** `BankAccount.__balance` and PIN hash storage.
- **Abstraction:** `BankAccount` is an abstract base class with abstract `withdraw()`.
- **Inheritance:** `SavingsAccount` and `CurrentAccount` inherit from `BankAccount`.
- **Polymorphism:** The ATM calls `withdraw()` on either account type; each class applies its own rules.

## Important
This is an educational demo, not production banking software. It has no real bank integration, ATM hardware, rate limiting, CSRF protection, audit controls, or production-grade deployment configuration. Change the Flask secret key before any deployment; use HTTPS and add appropriate security controls before exposing it publicly.
