from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.guards import require_login
from app.core.flash import flash
from app.db.session import SessionLocal
from app.services.auth_service import get_current_user
from app.models.company import Company

router = APIRouter(tags=["company"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/empresa/cadastrar", response_class=HTMLResponse)
def company_register_page(request: Request):
    guard = require_login(request, next_url="/empresa/cadastrar")
    if guard:
        return guard
    return tpl(request, "company_register.html")


@router.post("/empresa/cadastrar")
def company_register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    instagram: str = Form(""),
    description: str = Form(""),
):
    guard = require_login(request, next_url="/empresa/cadastrar")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()
    try:
        # já tem empresa vinculada?
        existing = db.execute(
            text("SELECT 1 FROM company_users WHERE user_id = :uid LIMIT 1"),
            {"uid": int(user.id)},
        ).fetchone()
        if existing:
            flash(request, "Você já tem uma empresa vinculada.", "error")
            return RedirectResponse("/", status_code=303)

        company = Company(
            name=name.strip(),
            email=(email or "").strip(),
            phone=(phone or "").strip() or None,
            address=(address or "").strip() or None,
            website=(website or "").strip() or None,
            instagram=(instagram or "").strip() or None,
            description=(description or "").strip() or None,
            status="pending",
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        # vínculo do usuário como owner
        db.execute(
            text("INSERT INTO company_users (company_id, user_id, role) VALUES (:cid, :uid, 'owner')"),
            {"cid": int(company.id), "uid": int(user.id)},
        )
        db.commit()

    finally:
        db.close()

    flash(request, "Empresa cadastrada! Aguardando aprovação do admin.", "ok")
    return RedirectResponse("/", status_code=303)