import enum
from sqlalchemy import String, ForeignKey, Numeric, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from .base import Base

class Currency(enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    # Add others as needed

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    currency: Mapped[Currency] = mapped_column(SqlEnum(Currency))
    
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="account")

    def __repr__(self):
        return f"<Account {self.name} ({self.currency.value})>"

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    
    description: Mapped[str] = mapped_column(String(255))
    
    # We store money as Numeric for precision, not Float
    original_value: Mapped[float] = mapped_column(Numeric(10, 2))
    original_currency: Mapped[Currency] = mapped_column(SqlEnum(Currency))
    
    value_in_account_currency: Mapped[float] = mapped_column(Numeric(10, 2))
    
    # Note: Added date because an expense tracker needs it, even if not explicitly requested
    date_str: Mapped[str] = mapped_column(String(20)) 

    account: Mapped["Account"] = relationship(back_populates="transactions")