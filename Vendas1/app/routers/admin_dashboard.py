from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.rbac_service import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get(
    "",
    response_class=HTMLResponse,
    dependencies=[Depends(require_permission("admin.dashboard.view"))],
)
def admin_dashboard(request: Request):
    db: Session = SessionLocal()

    try:
        # Totais gerais
        total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        total_orders = db.execute(text("SELECT COUNT(*) FROM orders")).scalar() or 0
        total_revenue = db.execute(text("SELECT COALESCE(SUM(total), 0) FROM orders")).scalar() or 0

        avg_ticket = 0.0
        if int(total_orders) > 0:
            avg_ticket = float(total_revenue) / float(total_orders)

        # Hoje (SQLite)
        orders_today = db.execute(
            text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now')")
        ).scalar() or 0

        revenue_today = db.execute(
            text("SELECT COALESCE(SUM(total), 0) FROM orders WHERE DATE(created_at) = DATE('now')")
        ).scalar() or 0

        # Últimos 7 dias
        orders_7d = db.execute(
            text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= DATE('now', '-7 day')")
        ).scalar() or 0

        revenue_7d = db.execute(
            text("SELECT COALESCE(SUM(total), 0) FROM orders WHERE DATE(created_at) >= DATE('now', '-7 day')")
        ).scalar() or 0

        # Últimos 30 dias
        orders_30d = db.execute(
            text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= DATE('now', '-30 day')")
        ).scalar() or 0

        revenue_30d = db.execute(
            text("SELECT COALESCE(SUM(total), 0) FROM orders WHERE DATE(created_at) >= DATE('now', '-30 day')")
        ).scalar() or 0

        # Agrupamento por status
        status_rows = db.execute(
            text(
                """
                SELECT COALESCE(status, 'novo') AS status, COUNT(*) AS qtd
                FROM orders
                GROUP BY COALESCE(status, 'novo')
                ORDER BY qtd DESC
                """
            )
        ).fetchall()

        orders_by_status = [{"status": r[0], "qtd": int(r[1])} for r in status_rows]

    finally:
        db.close()

    return tpl(
        request,
        "admin_dashboard.html",
        {
            "total_users": int(total_users),
            "total_orders": int(total_orders),
            "total_revenue": float(total_revenue),
            "avg_ticket": float(avg_ticket),
            "orders_today": int(orders_today),
            "revenue_today": float(revenue_today),
            "orders_7d": int(orders_7d),
            "revenue_7d": float(revenue_7d),
            "orders_30d": int(orders_30d),
            "revenue_30d": float(revenue_30d),
            "orders_by_status": orders_by_status,
        },
    )