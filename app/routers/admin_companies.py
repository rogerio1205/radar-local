from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.rbac_service import require_permission

router = APIRouter(prefix="/admin", tags=["admin-companies"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get(
    "/empresas",
    response_class=HTMLResponse,
    dependencies=[Depends(require_permission("admin.dashboard.view"))],
)
def admin_companies(request: Request):
    db: Session = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT id, name, email, status, created_at
                FROM companies
                ORDER BY id DESC
                """
            )
        ).fetchall()

        companies = [
            {"id": r[0], "name": r[1], "email": r[2], "status": r[3], "created_at": r[4]}
            for r in rows
        ]

        total = db.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
        pending = db.execute(text("SELECT COUNT(*) FROM companies WHERE status='pending'")).scalar() or 0
        approved = db.execute(text("SELECT COUNT(*) FROM companies WHERE status='approved'")).scalar() or 0
        blocked = db.execute(text("SELECT COUNT(*) FROM companies WHERE status='blocked'")).scalar() or 0

    finally:
        db.close()

    return tpl(
        request,
        "admin_companies.html",
        {
            "companies": companies,
            "total": int(total),
            "pending": int(pending),
            "approved": int(approved),
            "blocked": int(blocked),
        },
    )


@router.post(
    "/empresas/{company_id}/aprovar",
    dependencies=[Depends(require_permission("admin.dashboard.view"))],
)
def admin_company_approve(company_id: int):
    db: Session = SessionLocal()
    try:
        db.execute(text("UPDATE companies SET status='approved' WHERE id=:id"), {"id": int(company_id)})
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/empresas", status_code=303)


@router.post(
    "/empresas/{company_id}/bloquear",
    dependencies=[Depends(require_permission("admin.dashboard.view"))],
)
def admin_company_block(company_id: int):
    db: Session = SessionLocal()
    try:
        db.execute(text("UPDATE companies SET status='blocked' WHERE id=:id"), {"id": int(company_id)})
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/empresas", status_code=303)