from pathlib import Path
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: Optional[str] = None
    price: float = 0.0
    quantity: int = 0

    invoice_items: List["InvoiceItem"] = Relationship(back_populates="item")

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None

    invoices: List["Invoice"] = Relationship(back_populates="customer")

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[int] = Field(default=None, foreign_key="customer.id")
    total: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    customer: Optional[Customer] = Relationship(back_populates="invoices")
    items: List["InvoiceItem"] = Relationship(back_populates="invoice")

class InvoiceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: Optional[int] = Field(default=None, foreign_key="invoice.id")
    item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    quantity: int = 1
    unit_price: float = 0.0

    invoice: Optional[Invoice] = Relationship(back_populates="items")
    item: Optional[Item] = Relationship(back_populates="invoice_items")
