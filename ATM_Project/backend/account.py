from abc import ABC, abstractmethod


class BankAccount(ABC):
    """Abstract base class for bank accounts."""

    def __init__(self, account_number: str, holder_name: str, balance: float):
        self.account_number = account_number
        self.holder_name = holder_name
        self.__balance = float(balance)  # Encapsulation

    @property
    def balance(self):
        return self.__balance

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        self.__balance += amount
        return self.__balance

    @abstractmethod
    def withdraw(self, amount: float):
        """Each account type implements its own withdrawal rules."""
        raise NotImplementedError

    def _deduct(self, amount: float):
        self.__balance -= amount
        return self.__balance


class SavingsAccount(BankAccount):
    """Savings account with a minimum-balance rule."""

    MINIMUM_BALANCE = 500.0

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        if self.balance - amount < self.MINIMUM_BALANCE:
            raise ValueError(
                f"Keep at least ₹{self.MINIMUM_BALANCE:.2f} in your savings account."
            )
        return self._deduct(amount)


class CurrentAccount(BankAccount):
    """Current account demo; permits withdrawal up to the available balance."""

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        return self._deduct(amount)
