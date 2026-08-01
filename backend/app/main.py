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

# PDF & email deps
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import io
from fastapi.responses import StreamingResponse
import smtplib
from email.message import EmailMessage

app = FastAPI(title="Tally Workaround API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class StockAdd(BaseModel):
    amount: int

class InvoiceItemIn(BaseModel):
    item_id: int
    quantity: int

class InvoiceCreate(BaseModel):
    customer_name: Optional[str]
    customer_email: Optional[str]
    items: List[InvoiceItemIn]

class EmailRequest(BaseModel):
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None

# Template paths
ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

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
    # initialize tracking fields
    item.total_added = payload.quantity if hasattr(item, "total_added") else payload.quantity
    item.sold_count = getattr(item, "sold_count", 0)
    with get_session() as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

@app.post("/api/items/{item_id}/add_stock", response_model=Item)
def add_stock(item_id: int, payload: StockAdd):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    with get_session() as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.quantity += payload.amount
        # increment total_added if field exists
        if hasattr(item, "total_added"):
            item.total_added += payload.amount
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

@app.get("/api/items/summary")
def items_summary():
    with get_session() as session:
        items = session.exec(select(Item)).all()
        return [
            {
                "id": i.id,
                "name": i.name,
                "total_added": getattr(i, "total_added", 0),
                "sold_count": getattr(i, "sold_count", 0),
                "remaining": i.quantity,
            }
            for i in items
        ]

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

def render_invoice_pdf_bytes(invoice, invoice_items):
    # Render HTML using template if available
    if TEMPLATES_DIR.exists():
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html"]))
        try:
            template = env.get_template("invoice.html")
            html_out = template.render(invoice=invoice, items=invoice_items)
        except Exception:
            # fallback
            rows = "".join(
                f"<tr><td>{(it.item.name if it.item else it.item_id)}</td><td>{it.quantity}</td><td>{it.unit_price:.2f}</td><td>{it.quantity * it.unit_price:.2f}</td></tr>"
                for it in invoice_items
            )
            html_out = f"""
            <html><body>
            <h1>Invoice #{invoice.id}</h1>
            <p>Date: {invoice.created_at}</p>
            <p>Customer: {invoice.customer.name if invoice.customer else 'N/A'}</p>
            <table border='1' cellpadding='4' cellspacing='0'>
              <tr><th>Item</th><th>Qty</th><th>Unit</th><th>Total</th></tr>
              {rows}
            </table>
            <h3>Total: {invoice.total:.2f}</h3>
            </body></html>
            """
    else:
        rows = "".join(
            f"<tr><td>{(it.item.name if it.item else it.item_id)}</td><td>{it.quantity}</td><td>{it.unit_price:.2f}</td><td>{it.quantity * it.unit_price:.2f}</td></tr>"
            for it in invoice_items
        )
        html_out = f"""
        <html><body>
        <h1>Invoice #{invoice.id}</h1>
        <p>Date: {invoice.created_at}</p>
        <p>Customer: {invoice.customer.name if invoice.customer else 'N/A'}</p>
        <table border='1' cellpadding='4' cellspacing='0'>
          <tr><th>Item</th><th>Qty</th><th>Unit</th><th>Total</th></tr>
          {rows}
        </table>
        <h3>Total: {invoice.total:.2f}</h3>
        </body></html>
        """
    pdf_bytes = HTML(string=html_out).write_pdf()
    return pdf_bytes

@app.get("/api/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int):
    with get_session() as session:
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        items = session.exec(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)).all()
        pdf = render_invoice_pdf_bytes(invoice, items)
        return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{invoice.id}.pdf"})

@app.post("/api/invoices/{invoice_id}/email")
def email_invoice(invoice_id: int, req: EmailRequest):
    with get_session() as session:
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        items = session.exec(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)).all()
        pdf = render_invoice_pdf_bytes(invoice, items)

        to_addr = req.to or (invoice.customer.email if invoice.customer else None)
        if not to_addr:
            raise HTTPException(status_code=400, detail="No recipient email provided")

        subject = req.subject or f"Invoice #{invoice.id}"
        body = req.body or f"Please find attached invoice #{invoice.id} (total: {invoice.total:.2f})"

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = os.environ.get("SMTP_FROM") or os.environ.get("EMAIL_FROM")
        msg['To'] = to_addr
        msg.set_content(body)
        msg.add_attachment(pdf, maintype='application', subtype='pdf', filename=f"invoice_{invoice.id}.pdf")

        host = os.environ.get("SMTP_HOST")
        port = int(os.environ.get("SMTP_PORT", "465"))
        user = os.environ.get("SMTP_USER")
        password = os.environ.get("SMTP_PASSWORD")

        if not host:
            raise HTTPException(status_code=500, detail="SMTP_HOST not configured")

        # Use SSL connection
        try:
            with smtplib.SMTP_SSL(host, port) as s:
                if user and password:
                    s.login(user, password)
                s.send_message(msg)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

        return {"ok": True, "sent_to": to_addr}

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
            # deduct stock and increment sold_count if available
            item.quantity -= it.quantity
            if hasattr(item, "sold_count"):
                item.sold_count += it.quantity
            session.add(item)
            total += line_total

        invoice.total = total
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        return invoice

# Serve frontend static files from project frontend/ directory (mounted after API routes so /api/* matches first)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    # When running as a script, run uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
