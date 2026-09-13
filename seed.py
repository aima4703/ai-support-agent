"""
Run this once to fill the database with some fake data to test with.

Usage:
    python seed.py
"""

from datetime import date
from database import engine, SessionLocal, Base
from models import Customer, Order

# Create the tables if they don't exist yet
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Avoid inserting duplicates if you run this script twice
if db.query(Customer).count() == 0:
    alice = Customer(name="Alice Khan", email="alice@example.com")
    bob = Customer(name="Bob Malik", email="bob@example.com")
    db.add_all([alice, bob])
    db.commit()
    db.refresh(alice)
    db.refresh(bob)

    orders = [
        Order(
            id=4582,
            customer_id=alice.id,
            product="Wireless Headphones",
            status="shipped",
            order_date=date(2026, 9, 8),
            delivery_date=date(2026, 9, 15),
            price=59.99,
        ),
        Order(
            id=4583,
            customer_id=bob.id,
            product="Laptop Stand",
            status="processing",
            order_date=date(2026, 9, 12),
            delivery_date=None,
            price=24.50,
        ),
        Order(
            id=4584,
            customer_id=alice.id,
            product="USB-C Cable (2m)",
            status="delivered",
            order_date=date(2026, 8, 20),
            delivery_date=date(2026, 8, 25),
            price=9.99,
        ),
    ]
    db.add_all(orders)
    db.commit()
    print("Seeded 2 customers and 3 orders.")
else:
    print("Data already exists — skipping seed.")

db.close()
