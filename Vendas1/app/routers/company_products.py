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
from app.models.product import Product
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/empresa", tags=["empresa-produtos"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _get_user_company(db: Session, user_id: int):
    row = db.execute(
        text(
            """
            SELECT c.id, c.name
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

    company_id = int(row[0])
    company = db.query(Company).filter(Company.id == company_id).first()
    return company


def _save_product_image(image: UploadFile | None) -> str | None:
    if not image or not image.filename:
        return None

    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join("static", "uploads", "produtos", filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return filename


@router.get("/produtos", response_class=HTMLResponse)
def company_products_list(request: Request):
    guard = require_login(request, next_url="/empresa/produtos")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/empresa/produtos", status_code=303)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))
        if not empresa:
            flash(request, "Você ainda não possui empresa cadastrada.", "error")
            return RedirectResponse("/empresa/cadastrar", status_code=303)

        produtos = (
            db.query(Product)
            .filter(Product.company_id == int(empresa.id))
            .order_by(Product.id.desc())
            .all()
        )

        return tpl(
            request,
            "empresa_produtos.html",
            {
                "empresa": empresa,
                "empresa_id": int(empresa.id),
                "produtos": produtos,
            },
        )
    finally:
        db.close()


@router.get("/produtos/novo", response_class=HTMLResponse)
def company_products_new_page(request: Request):
    guard = require_login(request, next_url="/empresa/produtos/novo")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/empresa/produtos/novo", status_code=303)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))
        if not empresa:
            flash(request, "Você ainda não possui empresa cadastrada.", "error")
            return RedirectResponse("/empresa/cadastrar", status_code=303)

        return tpl(
            request,
            "empresa_produto_form.html",
            {
                "empresa": empresa,
                "empresa_id": int(empresa.id),
                "mode": "create",
                "produto": None,
            },
        )
    finally:
        db.close()


@router.post("/produtos/novo")
def company_products_create(
    request: Request,
    code: str = Form(""),
    name: str = Form(...),
    category: str = Form(""),
    description: str = Form(""),
    unit: str = Form("un"),
    weight: str = Form(""),
    price: float = Form(...),
    stock: int = Form(0),
    min_stock: int = Form(0),
    image: UploadFile | None = File(None),
    active: bool = Form(True),
):
    guard = require_login(request, next_url="/empresa/produtos/novo")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/empresa/produtos/novo", status_code=303)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))
        if not empresa:
            flash(request, "Você ainda não possui empresa cadastrada.", "error")
            return RedirectResponse("/empresa/cadastrar", status_code=303)

        filename = _save_product_image(image)

        p = Product(
            company_id=int(empresa.id),
            code=(code or "").strip() or None,
            name=name.strip(),
            category=(category or "").strip() or None,
            description=(description or "").strip() or None,
            unit=(unit or "").strip() or "un",
            weight=(weight or "").strip() or None,
            price=float(price),
            stock=int(stock),
            min_stock=int(min_stock),
            image=filename,
            active=bool(active),
        )
        db.add(p)
        db.commit()

    finally:
        db.close()

    flash(request, "Produto cadastrado!", "ok")
    return RedirectResponse(url="/empresa/produtos", status_code=303)


@router.get("/produtos/{produto_id}/editar", response_class=HTMLResponse)
def company_products_edit_page(request: Request, produto_id: int):
    guard = require_login(request, next_url=f"/empresa/produtos/{produto_id}/editar")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse(f"/login?next=/empresa/produtos/{produto_id}/editar", status_code=303)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))
        if not empresa:
            flash(request, "Empresa não encontrada.", "error")
            return RedirectResponse("/empresa/dashboard", status_code=303)

        produto = db.query(Product).filter(Product.id == int(produto_id)).first()

        if not produto:
            flash(request, "Produto não encontrado.", "error")
            return RedirectResponse("/empresa/produtos", status_code=303)

        if int(produto.company_id or 0) != int(empresa.id):
            flash(request, "Você não pode editar este produto.", "error")
            return RedirectResponse("/empresa/produtos", status_code=303)

        return tpl(
            request,
            "empresa_produto_form.html",
            {
                "empresa": empresa,
                "empresa_id": int(empresa.id),
                "produto": produto,
                "mode": "edit",
            },
        )
    finally:
        db.close()


@router.post("/produtos/{produto_id}/editar")
def company_products_update(
    request: Request,
    produto_id: int,
    code: str = Form(""),
    name: str = Form(...),
    category: str = Form(""),
    description: str = Form(""),
    unit: str = Form("un"),
    weight: str = Form(""),
    price: float = Form(...),
    stock: int = Form(0),
    min_stock: int = Form(0),
    image: UploadFile | None = File(None),
    active: bool = Form(False),
):
    guard = require_login(request, next_url=f"/empresa/produtos/{produto_id}/editar")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse(f"/login?next=/empresa/produtos/{produto_id}/editar", status_code=303)

    db: Session = SessionLocal()
    try:
        empresa = _get_user_company(db, int(user.id))
        if not empresa:
            flash(request, "Empresa não encontrada.", "error")
            return RedirectResponse("/empresa/dashboard", status_code=303)

        produto = db.query(Product).filter(Product.id == int(produto_id)).first()

        if not produto:
            flash(request, "Produto não encontrado.", "error")
            return RedirectResponse("/empresa/produtos", status_code=303)

        if int(produto.company_id or 0) != int(empresa.id):
            flash(request, "Você não pode editar este produto.", "error")
            return RedirectResponse("/empresa/produtos", status_code=303)

        filename = _save_product_image(image)
        if filename:
            produto.image = filename

        produto.code = (code or "").strip() or None
        produto.name = name.strip()
        produto.category = (category or "").strip() or None
        produto.description = (description or "").strip() or None
        produto.unit = (unit or "").strip() or "un"
        produto.weight = (weight or "").strip() or None
        produto.price = float(price)
        produto.stock = int(stock)
        produto.min_stock = int(min_stock)
        produto.active = bool(active)

        db.commit()

    finally:
        db.close()

    flash(request, "Produto atualizado!", "ok")
    return RedirectResponse("/empresa/produtos", status_code=303)


@router.get("/{empresa_id}/produtos", response_class=HTMLResponse)
def company_products_list_legacy(request: Request, empresa_id: int):
    return RedirectResponse("/empresa/produtos", status_code=303)


@router.get("/{empresa_id}/produtos/novo", response_class=HTMLResponse)
def company_products_new_page_legacy(request: Request, empresa_id: int):
    return RedirectResponse("/empresa/produtos/novo", status_code=303)


@router.post("/{empresa_id}/produtos/novo")
def company_products_create_legacy(request: Request, empresa_id: int):
    return RedirectResponse("/empresa/produtos/novo", status_code=303)