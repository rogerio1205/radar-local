from typing import Optional

from fastapi import APIRouter, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import SessionLocal
from app.models.product import Product

router = APIRouter(prefix="/api", tags=["api"])


def product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "company_id": p.company_id,
        "name": p.name,
        "category": p.category,
        "weight": p.weight,
        "price": float(p.price),
        "stock": int(p.stock),
        "active": bool(p.active),
    }


@router.post("/products")
def create_product(
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    category: str = Form(""),
    weight: str = Form(""),
    active: bool = Form(True),
):
    db: Session = SessionLocal()
    try:
        p = Product(
            name=name.strip(),
            price=float(price),
            stock=int(stock),
            category=(category or "").strip() or None,
            weight=(weight or "").strip() or None,
            active=bool(active),
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        return product_to_dict(p)
    finally:
        db.close()


@router.get("/products")
def list_products(
    q: Optional[str] = Query(default=None),
    only_active: bool = Query(default=True),
):
    db: Session = SessionLocal()
    try:
        query = db.query(Product)

        if only_active:
            query = query.filter(Product.active == True)  # noqa

        if q:
            like = f"%{q}%"
            query = query.filter(Product.name.ilike(like))

        items = query.order_by(desc(Product.id)).all()
        return [product_to_dict(p) for p in items]
    finally:
        db.close()