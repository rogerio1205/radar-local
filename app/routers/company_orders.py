from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.guards import require_login
from app.core.flash import flash
from app.db.session import SessionLocal
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/empresa", tags=["empresa-pedidos"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/pedidos", response_class=HTMLResponse)
def empresa_pedidos(
    request: Request,
    data_inicial: str = Query(default=""),
    data_final: str = Query(default=""),
    cliente: str = Query(default=""),
    status: str = Query(default=""),
):

    guard = require_login(request, next_url="/empresa/pedidos")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()

    try:

        sql = """
            SELECT
                id,
                customer_name,
                customer_phone,
                total,
                status,
                created_at
            FROM orders
            WHERE user_id = :uid
        """

        params = {"uid": int(user.id)}

        if cliente.strip():
            sql += """
                AND (
                    lower(customer_name) LIKE :cliente
                    OR lower(COALESCE(customer_phone, '')) LIKE :cliente
                )
            """
            params["cliente"] = f"%{cliente.strip().lower()}%"

        if status.strip():
            sql += " AND status = :status "
            params["status"] = status.strip()

        if data_inicial.strip():
            sql += " AND date(created_at) >= :data_inicial "
            params["data_inicial"] = data_inicial.strip()

        if data_final.strip():
            sql += " AND date(created_at) <= :data_final "
            params["data_final"] = data_final.strip()

        sql += " ORDER BY id DESC "

        rows = db.execute(text(sql), params).fetchall()

        pedidos = []

        for r in rows:
            pedidos.append(
                {
                    "id": r[0],
                    "customer": r[1],
                    "phone": r[2],
                    "total": float(r[3]),
                    "status": r[4],
                    "created_at": r[5],
                }
            )

        return tpl(
            request,
            "empresa_pedidos.html",
            {
                "pedidos": pedidos,
                "filtros": {
                    "data_inicial": data_inicial,
                    "data_final": data_final,
                    "cliente": cliente,
                    "status": status,
                },
            },
        )

    finally:
        db.close()


@router.post("/pedidos/status")
def empresa_pedido_status(
    request: Request,
    order_id: int = Form(...),
    status: str = Form(...),
):

    guard = require_login(request, next_url="/empresa/pedidos")
    if guard:
        return guard

    db: Session = SessionLocal()

    try:

        db.execute(
            text(
                """
                UPDATE orders
                SET status = :status
                WHERE id = :id
                """
            ),
            {"status": status, "id": int(order_id)},
        )

        db.commit()

    finally:
        db.close()

    flash(request, "Status do pedido atualizado.", "ok")

    return RedirectResponse("/empresa/pedidos", status_code=303)