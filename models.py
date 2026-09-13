"""
Table definitions.

Each class here becomes one table in the database.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product = Column(String, nullable=False)
    status = Column(String, nullable=False)       # e.g. "shipped", "delivered", "processing"
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    price = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="orders")
