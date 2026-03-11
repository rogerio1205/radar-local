from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.order import Order
from app.models.company import Company
from app.models.user import User


# =========================================================
# HELPERS
# =========================================================

def _get_created_at_column():
    if hasattr(Order, "created_at"):
        return getattr(Order, "created_at")
    if hasattr(Order, "created_on"):
        return getattr(Order, "created_on")
    if hasattr(Order, "createdAt"):
        return getattr(Order, "createdAt")
    return None


def _get_status_column():
    if hasattr(Order, "status"):
        return getattr(Order, "status")
    return None


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


# =========================================================
# DASHBOARD ADMIN
# =========================================================

def get_admin_dashboard_metrics(db: Session) -> Dict[str, Any]:
    created_col = _get_created_at_column()
    order_status_col = _get_status_column()

    total_orders = _safe_int(db.query(func.count(Order.id)).scalar())
    total_users = _safe_int(db.query(func.count(User.id)).scalar())
    total_companies = _safe_int(db.query(func.count(Company.id)).scalar())

    approved_companies = _safe_int(
        db.query(func.count(Company.id))
        .filter(Company.status == "approved")
        .scalar()
    )

    pending_companies = _safe_int(
        db.query(func.count(Company.id))
        .filter(Company.status == "pending")
        .scalar()
    )

    inactive_companies = _safe_int(
        db.query(func.count(Company.id))
        .filter(Company.status == "inactive")
        .scalar()
    )

    orders_today = 0
    if created_col is not None:
        today = date.today()
        orders_today = _safe_int(
            db.query(func.count(Order.id))
            .filter(func.date(created_col) == str(today))
            .scalar()
        )

    status_counts: Dict[str, int] = {}
    if order_status_col is not None:
        rows = (
            db.query(order_status_col, func.count(Order.id))
            .group_by(order_status_col)
            .all()
        )
        for status, count in rows:
            key = str(status or "indefinido")
            status_counts[key] = _safe_int(count)

    return {
        "total_orders": total_orders,
        "orders_today": orders_today,
        "total_users": total_users,
        "total_companies": total_companies,
        "approved_companies": approved_companies,
        "pending_companies": pending_companies,
        "inactive_companies": inactive_companies,
        "status_counts": status_counts,
        "has_created_at": created_col is not None,
    }


def get_dashboard_daily_series(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    created_col = _get_created_at_column()

    if created_col is None:
        return []

    start_dt = datetime.now() - timedelta(days=days - 1)

    rows = (
        db.query(
            func.date(created_col).label("d"),
            func.count(Order.id).label("c")
        )
        .filter(created_col >= start_dt)
        .group_by(func.date(created_col))
        .all()
    )

    total_map = {str(d): _safe_int(c) for d, c in rows}

    out: List[Dict[str, Any]] = []
    for i in range(days):
        d = date.today() - timedelta(days=(days - 1 - i))
        ds = str(d)
        out.append(
            {
                "date": ds,
                "orders": _safe_int(total_map.get(ds, 0)),
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