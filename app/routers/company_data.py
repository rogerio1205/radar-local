import os
import shutil
import uuid

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.guards import require_login
from app.core.flash import flash
from app.db.session import SessionLocal
from app.models.company import Company
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/empresa", tags=["empresa-dados"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _get_user_company(db: Session, user_id: int):
    row = db.execute(
        text(
            """
            SELECT c.id
            FROM companies c
            JOIN company_users cu ON cu.company_id = c.id
            WHERE cu.user_id = :uid
            LIMIT 1
            """
        ),
        {"uid": int(user_id)},
    ).fetchone()

    if not row:
        return None

    return db.query(Company).filter(Company.id == int(row[0])).first()


def _save_company_logo(image: UploadFile | None) -> str | None:
    if not image or not image.filename:
        return None

    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join("static", "uploads", "logos", filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return filename


@router.get("/dados", response_class=HTMLResponse)
def empresa_dados(request: Request):
    guard = require_login(request, next_url="/empresa/dados")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))

        if not empresa:
            flash(request, "Empresa não encontrada.", "error")
            return RedirectResponse("/empresa/dashboard", status_code=303)

        return tpl(
            request,
            "empresa_dados.html",
            {
                "empresa": empresa,
            },
        )
    finally:
        db.close()


@router.post("/dados")
def empresa_dados_salvar(
    request: Request,
    phone: str = Form(""),
    whatsapp: str = Form(""),
    country: str = Form(""),
    state: str = Form(""),
    city: str = Form(""),
    neighborhood: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    instagram: str = Form(""),
    map_link: str = Form(""),
    pix_key: str = Form(""),
    specialties: str = Form(""),
    description: str = Form(""),
    latitude: str = Form(""),
    longitude: str = Form(""),
    logo_file: UploadFile | None = File(None),
):
    guard = require_login(request, next_url="/empresa/dados")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))

        if not empresa:
            flash(request, "Empresa não encontrada.", "error")
            return RedirectResponse("/empresa/dashboard", status_code=303)

        filename = _save_company_logo(logo_file)
        if filename:
            empresa.logo = filename

        empresa.phone = (phone or "").strip() or None
        empresa.whatsapp = (whatsapp or "").strip() or None
        empresa.country = (country or "").strip() or None
        empresa.state = (state or "").strip() or None
        empresa.city = (city or "").strip() or None
        empresa.neighborhood = (neighborhood or "").strip() or None
        empresa.address = (address or "").strip() or None
        empresa.website = (website or "").strip() or None
        empresa.instagram = (instagram or "").strip() or None
        empresa.map_link = (map_link or "").strip() or None
        empresa.pix_key = (pix_key or "").strip() or None
        empresa.specialties = (specialties or "").strip() or None
        empresa.description = (description or "").strip() or None
        empresa.latitude = (latitude or "").strip() or None
        empresa.longitude = (longitude or "").strip() or None

        db.commit()

    finally:
        db.close()

    flash(request, "Dados da empresa atualizados.", "ok")
    return RedirectResponse("/empresa/dados", status_code=303)