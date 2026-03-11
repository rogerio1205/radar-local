from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.rbac_service import require_permission
from app.core.flash import flash

router = APIRouter(prefix="/admin", tags=["admin"])

ALL_STATUSES = ["novo", "pago", "enviado", "concluido", "cancelado"]

def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)

@router.get(
    "/orders",
    response_class=HTMLResponse,
    dependencies=[Depends(require_permission("admin.orders.read"))],
)
def admin_orders(request: Request, status: str = "", q: str = "", page: int = 1):
    PAGE_SIZE = 10
    if page < 1:
        page = 1
    offset = (page - 1) * PAGE_SIZE

    status = (status or "").strip()
    q = (q or "").strip()

    where = ["1=1"]
    params = {}

    if status:
        where.append("COALESCE(status,'novo') = :st")
        params["st"] = status

    if q:
        if q.isdigit():
            where.append("id = :oid")
            params["oid"] = int(q)
        else:
            where.append("LOWER(customer_name) LIKE :q")
            params["q"] = f"%{q.lower()}%"

    where_sql = " AND ".join(where)

    db: Session = SessionLocal()
    try:
        total = db.execute(text(f"SELECT COUNT(*) FROM orders WHERE {where_sql}"), params).scalar() or 0

        rows = db.execute(
            text(
                f"""
                SELECT id, customer_name, total, COALESCE(status,'novo') as status,
                       payment_method, payment_status, created_at
                FROM orders
                WHERE {where_sql}
                ORDER BY id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": PAGE_SIZE, "offset": offset},
        ).fetchall()

        orders = [
            {
                "id": r[0],
                "customer_name": r[1],
                "total": float(r[2]),
                "status": r[3],
                "payment_method": r[4],
                "payment_status": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]

        total_pages = (total // PAGE_SIZE) + (1 if total % PAGE_SIZE > 0 else 0)
        if total_pages < 1:
            total_pages = 1

    finally:
        db.close()

    return tpl(
        request,
        "admin_orders.html",
        {
            "orders": orders,
            "all_statuses": ALL_STATUSES,
            "status_filter": status,
            "q": q,
            "page": page,
            "total_pages": total_pages,
        },
    )

@router.post(
    "/orders/{order_id}/status",
    dependencies=[Depends(require_permission("admin.orders.update"))],
)
def admin_update_order_status(request: Request, order_id: int, status: str = Form(...)):
    new_status = (status or "").strip()
    if new_status not in ALL_STATUSES:
        flash(request, "Status inválido", "error")
        return RedirectResponse("/admin/orders", status_code=303)

    db: Session = SessionLocal()
    try:
        db.execute(text("UPDATE orders SET status = :st WHERE id = :oid"), {"st": new_status, "oid": int(order_id)})
        db.commit()
    finally:
        db.close()

    flash(request, "Pedido atualizado.", "ok")
    return RedirectResponse("/admin/orders", status_code=303)