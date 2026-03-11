from fastapi import APIRouter, Request, Form
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
def empresa_pedidos(request: Request):

    guard = require_login(request, next_url="/empresa/pedidos")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()

    try:

        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    customer_name,
                    customer_phone,
                    total,
                    status,
                    created_at
                FROM orders
                WHERE user_id = :uid
                ORDER BY id DESC
                """
            ),
            {"uid": int(user.id)},
        ).fetchall()

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