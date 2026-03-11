from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.guards import require_login
from app.core.flash import flash
from app.db.session import SessionLocal
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/empresa", tags=["empresa-clientes"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/clientes", response_class=HTMLResponse)
def empresa_clientes(request: Request):

    guard = require_login(request, next_url="/empresa/clientes")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()

    try:

        rows = db.execute(
            text(
                """
                SELECT
                    customer_name,
                    customer_phone,
                    COUNT(*) as pedidos,
                    SUM(total) as total
                FROM orders
                WHERE user_id = :uid
                GROUP BY customer_name, customer_phone
                ORDER BY total DESC
                """
            ),
            {"uid": int(user.id)},
        ).fetchall()

        clientes = []

        for r in rows:

            clientes.append(
                {
                    "name": r[0],
                    "phone": r[1],
                    "orders": int(r[2]),
                    "total": float(r[3]),
                }
            )

        return tpl(
            request,
            "empresa_clientes.html",
            {
                "clientes": clientes,
            },
        )

    finally:
        db.close()