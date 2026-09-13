"""
The main FastAPI application.

Run it with:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs to try it in your browser.
"""

from dotenv import load_dotenv
load_dotenv()  # reads your .env file so GROQ_API_KEY is available

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import Order
from chat import chat_with_agent

app = FastAPI(title="AI Support Agent - Step 4: Chat UI")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def serve_chat_page():
    """Serves the simple chat webpage."""
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    """Simple endpoint to confirm the server is running."""
    return {"status": "ok"}


@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Look up one order by its ID and return its status."""
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail=f"Order #{order_id} not found")

    return {
        "order_id": order.id,
        "product": order.product,
        "status": order.status,
        "order_date": order.order_date,
        "delivery_date": order.delivery_date,
        "price": order.price,
        "customer": order.customer.name,
    }


@app.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Talk to the AI in plain English. It decides on its own whether
    it needs to look up an order to answer you."""
    reply = chat_with_agent(request.message, db)
    return {"reply": reply}
