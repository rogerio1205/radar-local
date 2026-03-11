from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.services.auth_service import get_current_user
from app.db.session import SessionLocal
from app.models.order import Order, OrderItem
from app.models.product import Product

router = APIRouter(prefix="/api", tags=["api"])

class OrderItemIn(BaseModel):
    product_id: int
    qty: int

class OrderCreateIn(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    items: List[OrderItemIn]

@router.post("/orders")
def create_order(request: Request, payload: OrderCreateIn):
    user = get_current_user(request)
    if not user:
        return {"error": "not authenticated"}

    db: Session = SessionLocal()
    try:
        total = 0.0
        items_to_save: list[tuple[Product, int, float]] = []

        for it in payload.items:
            p = db.query(Product).filter(Product.id == it.product_id).first()
            if not p:
                return {"error": f"Produto id {it.product_id} não existe"}
            if not p.active:
                return {"error": f"Produto id {it.product_id} está inativo"}
            if int(p.stock) < int(it.qty):
                return {"error": f"Estoque insuficiente para {p.name}. Disponível: {p.stock}"}

            qty = int(it.qty)
            unit_price = float(p.price)
            total += unit_price * qty
            items_to_save.append((p, qty, unit_price))

        order = Order(
            user_id=user.id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            status="novo",
            total=float(total),
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        for p, qty, unit_price in items_to_save:
            db.add(OrderItem(
                order_id=order.id,
                product_id=p.id,
                qty=qty,
                unit_price=unit_price,
                line_total=unit_price * qty,
            ))
            p.stock = int(p.stock) - int(qty)

        db.commit()
        return {"ok": True, "order_id": order.id, "total": float(total)}

    except Exception:
        db.rollback()
        return {"error": "Não foi possível finalizar o pedido (estoque pode ter mudado)."}
    finally:
        db.close()

@router.get("/orders")
def list_orders(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "not authenticated"}

    db: Session = SessionLocal()
    try:
        orders = (
            db.query(Order)
            .filter(Order.user_id == user.id)
            .order_by(Order.id.desc())
            .all()
        )
        return [{
            "id": o.id,
            "status": o.status,
            "total": float(o.total),
            "created_at": o.created_at.isoformat() if o.created_at else None,
        } for o in orders]
    finally:
        db.close()