from datetime import date, timedelta

from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.models.product import Product
from app.models.company import Company


def get_admin_dashboard_metrics(db: Session) -> dict:
    today = date.today()

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_companies = db.query(func.count(Company.id)).scalar() or 0

    paid_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status == "pago")
        .scalar()
        or 0
    )

    today_orders = (
        db.query(func.count(Order.id))
        .filter(cast(Order.created_at, Date) == today)
        .scalar()
        or 0
    )

    today_revenue = (
        db.query(func.coalesce(func.sum(Order.total), 0))
        .filter(cast(Order.created_at, Date) == today)
        .filter(Order.status == "pago")
        .scalar()
        or 0
    )

    pending_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status == "novo")
        .scalar()
        or 0
    )

    return {
        "total_orders": int(total_orders),
        "total_users": int(total_users),
        "total_products": int(total_products),
        "total_companies": int(total_companies),
        "paid_orders": int(paid_orders),
        "today_orders": int(today_orders),
        "today_revenue": float(today_revenue),
        "pending_orders": int(pending_orders),
    }


def get_dashboard_daily_series(db: Session, days: int = 7) -> list[dict]:
    days = int(days)
    start_date = date.today() - timedelta(days=days - 1)

    created_day = cast(Order.created_at, Date)

    rows = (
        db.query(
            created_day.label("day"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .filter(created_day >= start_date)
        .group_by(created_day)
        .order_by(created_day.asc())
        .all()
    )

    data_map = {
        row.day: {
            "orders": int(row.orders or 0),
            "revenue": float(row.revenue or 0),
        }
        for row in rows
    }

    series = []
    current = start_date

    for _ in range(days):
        item = data_map.get(current, {"orders": 0, "revenue": 0.0})
        series.append(
            {
                "date": current.isoformat(),
                "orders": item["orders"],
                "revenue": item["revenue"],
            }
        )
        current += timedelta(days=1)

    return series


def list_orders_admin(db: Session, status: str | None = None):
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    return query.order_by(Order.id.desc()).all()


def get_order_admin(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == int(order_id)).first()


def update_order_status_admin(db: Session, order_id: int, status: str) -> bool:
    order = db.query(Order).filter(Order.id == int(order_id)).first()

    if not order:
        return False

    order.status = status
    db.commit()
    db.refresh(order)

    return True