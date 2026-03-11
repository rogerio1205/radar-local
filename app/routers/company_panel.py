from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.guards import require_login
from app.core.flash import flash
from app.db.session import SessionLocal
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/empresa", tags=["empresa"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/dashboard", response_class=HTMLResponse)
def empresa_dashboard(request: Request):
    guard = require_login(request, next_url="/empresa/dashboard")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/empresa/dashboard", status_code=303)

    db: Session = SessionLocal()
    try:
        empresa = db.execute(
            text(
                """
                SELECT c.id, c.name, c.logo
                FROM companies c
                JOIN company_users cu ON cu.company_id = c.id
                WHERE cu.user_id = :uid
                LIMIT 1
                """
            ),
            {"uid": int(user.id)},
        ).fetchone()

        if not empresa:
            flash(request, "Você ainda não possui empresa cadastrada.", "error")
            return RedirectResponse("/empresa/cadastrar", status_code=303)

        empresa_id = int(empresa[0])
        empresa_nome = empresa[1]
        empresa_logo = empresa[2]

        total_produtos = db.execute(
            text("SELECT COUNT(*) FROM products WHERE company_id = :cid"),
            {"cid": empresa_id},
        ).scalar() or 0

        total_pedidos = 0
        total_clientes = 0
        total_vendido = 0.0
        ultimos_pedidos = []

        try:
            total_pedidos = db.execute(
                text("SELECT COUNT(*) FROM orders WHERE user_id = :uid"),
                {"uid": int(user.id)},
            ).scalar() or 0

            total_clientes = db.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT customer_phone)
                    FROM orders
                    WHERE user_id = :uid
                    """
                ),
                {"uid": int(user.id)},
            ).scalar() or 0

            total_vendido = db.execute(
                text(
                    """
                    SELECT COALESCE(SUM(total), 0)
                    FROM orders
                    WHERE user_id = :uid
                    """
                ),
                {"uid": int(user.id)},
            ).scalar() or 0

            rows = db.execute(
                text(
                    """
                    SELECT id, customer_name, total, status, created_at
                    FROM orders
                    WHERE user_id = :uid
                    ORDER BY id DESC
                    LIMIT 5
                    """
                ),
                {"uid": int(user.id)},
            ).fetchall()

            ultimos_pedidos = [
                {
                    "id": r[0],
                    "customer_name": r[1],
                    "total": float(r[2]),
                    "status": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]

        except Exception:
            total_pedidos = 0
            total_clientes = 0
            total_vendido = 0.0
            ultimos_pedidos = []

        return tpl(
            request,
            "empresa_dashboard.html",
            {
                "empresa_id": empresa_id,
                "empresa_nome": empresa_nome,
                "empresa_logo": empresa_logo,
                "total_produtos": int(total_produtos),
                "total_pedidos": int(total_pedidos),
                "total_clientes": int(total_clientes),
                "total_vendido": float(total_vendido),
                "ultimos_pedidos": ultimos_pedidos,
            },
        )
    finally:
        db.close()