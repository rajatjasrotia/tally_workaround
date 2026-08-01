from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import select
from .database import init_db, get_session
from .models import Item, Customer, Invoice, InvoiceItem
from pathlib import Path
from fastapi import Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

app = FastAPI(title="Tally Workaround API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files from project frontend/ directory
ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Pydantic schemas for requests
class ItemCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    price: float = 0.0
    quantity: int = 0

class ItemUpdate(BaseModel):
    name: Optional[str]
    sku: Optional[str]
    price: Optional[float]
    quantity: Optional[int]

class InvoiceItemIn(BaseModel):
    item_id: int
    quantity: int

class InvoiceCreate(BaseModel):
    customer_name: Optional[str]
    customer_email: Optional[str]
    items: List[InvoiceItemIn]

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/items", response_model=List[Item])
def list_items():
    with get_session() as session:
        items = session.exec(select(Item)).all()
        return items

@app.post("/api/items", response_model=Item)
def create_item(payload: ItemCreate):
    item = Item.from_orm(payload)
    with get_session() as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemUpdate):
    with get_session() as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item_data = payload.dict(exclude_unset=True)
        for k, v in item_data.items():
            setattr(item, k, v)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    with get_session() as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        session.delete(item)
        session.commit()
        return {"ok": True}

@app.get("/api/invoices", response_model=List[Invoice])
def list_invoices():
    with get_session() as session:
        invoices = session.exec(select(Invoice)).all()
        return invoices

@app.post("/api/invoices", response_model=Invoice)
def create_invoice(payload: InvoiceCreate):
    with get_session() as session:
        # Create or find customer
        customer = None
        if payload.customer_name:
            customer = session.exec(select(Customer).where(Customer.name == payload.customer_name)).first()
            if not customer:
                customer = Customer(name=payload.customer_name, email=payload.customer_email)
                session.add(customer)
                session.commit()
                session.refresh(customer)

        invoice = Invoice(customer_id=customer.id if customer else None, total=0.0)
        session.add(invoice)
        session.commit()
        session.refresh(invoice)

        total = 0.0
        for it in payload.items:
            item = session.get(Item, it.item_id)
            if not item:
                session.rollback()
                raise HTTPException(status_code=404, detail=f"Item {it.item_id} not found")
            if item.quantity < it.quantity:
                session.rollback()
                raise HTTPException(status_code=400, detail=f"Insufficient stock for item {item.name}")
            unit_price = item.price
            line_total = unit_price * it.quantity
            invoice_item = InvoiceItem(invoice_id=invoice.id, item_id=item.id, quantity=it.quantity, unit_price=unit_price)
            session.add(invoice_item)
            # deduct stock
            item.quantity -= it.quantity
            session.add(item)
            total += line_total

        invoice.total = total
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        return invoice

if __name__ == "__main__":
    # When running as a script, run uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
