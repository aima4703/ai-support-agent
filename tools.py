"""
This file holds the actual "work" functions the AI is allowed to use.

Keeping them separate from main.py means both the plain API endpoint
AND the AI agent can call the exact same function — we're not writing
the lookup logic twice.
"""

from sqlalchemy.orm import Session
from models import Order
from rag import search_policies


def lookup_order(order_id: int, db: Session) -> dict:
    """
    Looks up one order by ID.
    Returns a plain dictionary (not a database object) so it's easy
    to hand to the AI or turn into JSON.
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return {"error": f"No order found with ID {order_id}"}

    return {
        "order_id": order.id,
        "product": order.product,
        "status": order.status,
        "order_date": str(order.order_date),
        "delivery_date": str(order.delivery_date) if order.delivery_date else None,
        "price": order.price,
        "customer": order.customer.name,
    }


def search_policy(query: str) -> dict:
    """
    Searches the company's policy documents for the most relevant
    passages to answer the customer's question.
    """
    results = search_policies(query)
    return {"policy_excerpts": [r["text"] for r in results]}


# This describes the function above IN A FORMAT GROQ UNDERSTANDS.
# Think of it as a "menu" you hand to the AI: "here is a tool called
# lookup_order, it needs an order_id number, use it when relevant."
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order's status, product, and delivery info by its order ID number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The numeric order ID, e.g. 4582",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Search the store's return, refund, and shipping policy documents to answer questions about rules like return windows, refund eligibility, or shipping costs and times.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's question, e.g. 'can I return an item after 20 days?'",
                    }
                },
                "required": ["query"],
            },
        },
    },
]
