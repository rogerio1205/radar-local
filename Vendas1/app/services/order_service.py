from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Tuple

from app.models.product import Product
from app.models.order import Order, OrderItem


def _sqlite_begin_immediate(db: Session) -> None:
    """
    Em SQLite, isso reduz chance de concorrência/estoque negativo,
    pois pega um lock de escrita cedo.
    Em Postgres, usaremos SELECT ... FOR UPDATE no futuro.
    """
    if db.bind and db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))


def validate_and_price_items(db: Session, cart_items: List[Dict]) -> Tuple[float, List[Tuple[Product, int, float]]]:
    total = 0.0
    to_update: list[tuple[Product, int, float]] = []

    for item in cart_items:
        pid = int(item["product_id"])
        qty = int(item.get("qty", 1))

        p = db.query(Product).filter(Product.id == pid).first()
        if not p:
            raise ValueError(f"Produto {pid} não existe mais.")
        if not p.active:
            raise ValueError(f"Produto {p.name} está inativo.")
        if int(p.stock) < qty:
            raise ValueError(f"Estoque insuficiente para {p.name}. Disponível: {p.stock}")

        unit_price = float(p.price)
        total += unit_price * qty
        to_update.append((p, qty, unit_price))

    return total, to_update


def create_order_from_items(
    db: Session,
    user_id: int,
    customer_name: str,
    customer_phone: str,
    customer_address: str,
    payment_method: str | None,
    items: List[Tuple[Product, int, float]],
    status: str = "novo",
) -> Order:
    # ✅ transação
    _sqlite_begin_immediate(db)

    try:
        total = sum(unit_price * qty for _, qty, unit_price in items)

        order = Order(
            user_id=user_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            status=status,
            total=float(total),
            payment_method=(payment_method or None),
            payment_status="pendente" if payment_method else None,
        )
        db.add(order)
        db.flush()  # pega order.id sem commit

        # ✅ baixa estoque dentro da mesma transação
        for p, qty, unit_price in items:
            # revalidar estoque no momento do commit
            if int(p.stock) < int(qty):
                raise ValueError(f"Estoque insuficiente para {p.name}. Disponível: {p.stock}")

            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    qty=qty,
                    unit_price=unit_price,
                    line_total=unit_price * qty,
                )
            )
            p.stock = int(p.stock) - int(qty)

        db.commit()
        db.refresh(order)
        return order

    except Exception:
        db.rollback()
        raise