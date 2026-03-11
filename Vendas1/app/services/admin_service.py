from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.order import Order


# =========================================================
# HELPERS DE COMPATIBILIDADE
# =========================================================

def _get_created_at_column():
    if hasattr(Order, "created_at"):
        return getattr(Order, "created_at")
    if hasattr(Order, "created_on"):
        return getattr(Order, "created_on")
    if hasattr(Order, "createdAt"):
        return getattr(Order, "createdAt")
    return None


def _get_total_column():
    if hasattr(Order, "total"):
        return getattr(Order, "total")
    if hasattr(Order, "total_amount"):
        return getattr(Order, "total_amount")
    if hasattr(Order, "amount"):
        return getattr(Order, "amount")
    return None


def _get_status_column():
    if hasattr(Order, "status"):
        return getattr(Order, "status")
    return None


def _safe_float(v) -> float:
    try:
        return float(v or 0.0)
    except Exception:
        return 0.0


def _is_paid_status_expr():
    status_col = _get_status_column()
    if status_col is None:
        return False
    return (status_col == "pago") | (status_col == "paid")


# =========================================================
# DASHBOARD
# =========================================================

def get_admin_dashboard_metrics(db: Session) -> Dict[str, Any]:
    created_col = _get_created_at_column()
    total_col = _get_total_column()
    status_col = _get_status_column()

    now = datetime.now()
    today = date.today()

    total_orders = int(db.query(func.count(Order.id)).scalar() or 0)

    total_revenue = 0.0
    if total_col is not None and status_col is not None:
        total_revenue = _safe_float(
            db.query(func.coalesce(func.sum(total_col), 0.0))
            .filter(_is_paid_status_expr())
            .scalar()
        )

    orders_today = 0
    revenue_today = 0.0

    if created_col is not None:
        orders_today = int(
            db.query(func.count(Order.id))
            .filter(func.date(created_col) == str(today))
            .scalar()
            or 0
        )

        if total_col is not None and status_col is not None:
            revenue_today = _safe_float(
                db.query(func.coalesce(func.sum(total_col), 0.0))
                .filter(_is_paid_status_expr())
                .filter(func.date(created_col) == str(today))
                .scalar()
            )

    paid_last_7 = 0
    paid_last_30 = 0
    revenue_last_7 = 0.0
    revenue_last_30 = 0.0

    if created_col is not None and status_col is not None:
        dt_7 = now - timedelta(days=7)
        dt_30 = now - timedelta(days=30)

        paid_last_7 = int(
            db.query(func.count(Order.id))
            .filter(_is_paid_status_expr())
            .filter(created_col >= dt_7)
            .scalar()
            or 0
        )

        paid_last_30 = int(
            db.query(func.count(Order.id))
            .filter(_is_paid_status_expr())
            .filter(created_col >= dt_30)
            .scalar()
            or 0
        )

        if total_col is not None:
            revenue_last_7 = _safe_float(
                db.query(func.coalesce(func.sum(total_col), 0.0))
                .filter(_is_paid_status_expr())
                .filter(created_col >= dt_7)
                .scalar()
            )

            revenue_last_30 = _safe_float(
                db.query(func.coalesce(func.sum(total_col), 0.0))
                .filter(_is_paid_status_expr())
                .filter(created_col >= dt_30)
                .scalar()
            )

    ticket_medio = 0.0
    if total_orders > 0:
        ticket_medio = float(total_revenue) / float(total_orders)

    status_counts: Dict[str, int] = {}
    if status_col is not None:
        rows = db.query(status_col, func.count(Order.id)).group_by(status_col).all()
        for s, c in rows:
            key = str(s or "indefinido")
            status_counts[key] = int(c or 0)

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "orders_today": int(orders_today),
        "revenue_today": float(revenue_today),
        "paid_last_7": int(paid_last_7),
        "paid_last_30": int(paid_last_30),
        "revenue_last_7": float(revenue_last_7),
        "revenue_last_30": float(revenue_last_30),
        "ticket_medio": float(ticket_medio),
        "status_counts": status_counts,
        "has_created_at": created_col is not None,
        "has_total": total_col is not None,
    }


def get_dashboard_daily_series(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    created_col = _get_created_at_column()
    total_col = _get_total_column()
    status_col = _get_status_column()

    if created_col is None:
        return []

    start_dt = datetime.now() - timedelta(days=days - 1)

    total_rows = (
        db.query(func.date(created_col).label("d"), func.count(Order.id).label("c"))
        .filter(created_col >= start_dt)
        .group_by(func.date(created_col))
        .all()
    )
    total_map = {str(d): int(c or 0) for d, c in total_rows}

    paid_map = {}
    rev_map = {}

    if status_col is not None:
        paid_rows = (
            db.query(func.date(created_col).label("d"), func.count(Order.id).label("c"))
            .filter(created_col >= start_dt)
            .filter(_is_paid_status_expr())
            .group_by(func.date(created_col))
            .all()
        )
        paid_map = {str(d): int(c or 0) for d, c in paid_rows}

        if total_col is not None:
            rev_rows = (
                db.query(func.date(created_col).label("d"), func.coalesce(func.sum(total_col), 0.0).label("s"))
                .filter(created_col >= start_dt)
                .filter(_is_paid_status_expr())
                .group_by(func.date(created_col))
                .all()
            )
            rev_map = {str(d): _safe_float(s) for d, s in rev_rows}

    out: List[Dict[str, Any]] = []
    for i in range(days):
        d = date.today() - timedelta(days=(days - 1 - i))
        ds = str(d)
        out.append(
            {
                "date": ds,
                "orders": int(total_map.get(ds, 0)),
                "paid_orders": int(paid_map.get(ds, 0)),
                "revenue": float(rev_map.get(ds, 0.0)),
            }
        )

    return out


# =========================================================
# PEDIDOS ADMIN
# =========================================================

def list_orders_admin(db: Session, status: Optional[str] = None):
    query = db.query(Order)

    status_col = _get_status_column()
    if status and status_col is not None:
        query = query.filter(status_col == status)

    created_col = _get_created_at_column()
    if created_col is not None:
        query = query.order_by(created_col.desc())
    else:
        query = query.order_by(Order.id.desc())

    return query.all()


def get_order_admin(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == int(order_id)).first()


def update_order_status_admin(db: Session, order_id: int, status: str) -> bool:
    order = db.query(Order).filter(Order.id == int(order_id)).first()
    if not order:
        return False

    if hasattr(order, "status"):
        order.status = status
        db.commit()
        return True

    return False