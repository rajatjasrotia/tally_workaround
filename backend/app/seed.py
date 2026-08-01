from .database import get_session
from .models import Item

def seed_data():
    session = get_session()
    items = [
        Item(name="Widget A", sku="WIDGET-A", price=10.0, quantity=100),
        Item(name="Widget B", sku="WIDGET-B", price=15.5, quantity=50),
        Item(name="Widget C", sku="WIDGET-C", price=7.25, quantity=200),
    ]
    for it in items:
        session.add(it)
    session.commit()

if __name__ == "__main__":
    from .database import init_db
    init_db()
    seed_data()
    print("Seeded sample data")
