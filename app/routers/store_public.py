from urllib.parse import quote_plus

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.flash import flash
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.product import Product

from app.services.auth_service import get_current_user
from app.services.cart_service import add_to_cart

router = APIRouter(tags=["store-public"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_google_maps_link(company: Company) -> str:
    if _safe_text(company.latitude) and _safe_text(company.longitude):
        return f"https://www.google.com/maps?q={quote_plus(f'{company.latitude},{company.longitude}')}"  # noqa

    query_parts = [
        _safe_text(company.name),
        _safe_text(company.address),
        _safe_text(company.city),
        _safe_text(company.state),
    ]
    query = ", ".join([p for p in query_parts if p]) or "Brasil"
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def _build_waze_link(company: Company) -> str:
    if _safe_text(company.latitude) and _safe_text(company.longitude):
        return f"https://waze.com/ul?ll={quote_plus(f'{company.latitude},{company.longitude}')}&navigate=yes"  # noqa

    query_parts = [
        _safe_text(company.name),
        _safe_text(company.address),
        _safe_text(company.city),
        _safe_text(company.state),
    ]
    query = ", ".join([p for p in query_parts if p]) or "Brasil"
    return f"https://waze.com/ul?q={quote_plus(query)}&navigate=yes"


@router.get("/loja/{empresa_id}", response_class=HTMLResponse)
def public_store_page(request: Request, empresa_id: int):
    user = get_current_user(request)

    db: Session = SessionLocal()

    try:
        empresa = db.query(Company).filter(Company.id == int(empresa_id)).first()

        if not empresa:
            flash(request, "Loja não encontrada.", "error")
            return RedirectResponse("/", status_code=303)

        produtos = (
            db.query(Product)
            .filter(Product.company_id == int(empresa_id))
            .filter(Product.active == True)  # noqa
            .order_by(Product.id.desc())
            .all()
        )

        return tpl(
            request,
            "store_public.html",
            {
                "company": empresa,
                "products": produtos,
                "current_user": user,
                "user_logged": True if user else False,
            },
        )

    finally:
        db.close()


@router.get("/rota-loja/{empresa_id}", response_class=HTMLResponse)
def public_store_route_options(request: Request, empresa_id: int):
    user = get_current_user(request)

    if not user:
        flash(request, "Faça login para traçar rota até a loja.", "error")
        return RedirectResponse(f"/login?next=/rota-loja/{empresa_id}", status_code=303)

    db: Session = SessionLocal()

    try:
        empresa = db.query(Company).filter(Company.id == int(empresa_id)).first()

        if not empresa:
            flash(request, "Loja não encontrada.", "error")
            return RedirectResponse("/", status_code=303)

        google_maps_link = _safe_text(empresa.map_link) or _build_google_maps_link(empresa)
        waze_link = _build_waze_link(empresa)

        return tpl(
            request,
            "route_options.html",
            {
                "company": empresa,
                "google_maps_link": google_maps_link,
                "waze_link": waze_link,
                "current_user": user,
            },
        )

    finally:
        db.close()


@router.post("/loja/{empresa_id}/cart/add")
def public_store_add_to_cart(
    request: Request,
    empresa_id: int,
    product_id: int = Form(...),
    qty: int = Form(...),
):
    user = get_current_user(request)

    if not user:
        flash(
            request,
            "Para comprar nesta loja, faça login ou crie sua conta.",
            "error",
        )
        return RedirectResponse(f"/login?next=/loja/{empresa_id}", status_code=303)

    db: Session = SessionLocal()

    try:
        empresa = db.query(Company).filter(Company.id == int(empresa_id)).first()

        if not empresa:
            flash(request, "Loja não encontrada.", "error")
            return RedirectResponse("/", status_code=303)

        produto = (
            db.query(Product)
            .filter(Product.id == int(product_id))
            .filter(Product.company_id == int(empresa_id))
            .first()
        )

        if not produto:
            flash(request, "Produto não encontrado.", "error")
            return RedirectResponse(f"/loja/{empresa_id}", status_code=303)

        if not produto.active:
            flash(request, "Produto inativo.", "error")
            return RedirectResponse(f"/loja/{empresa_id}", status_code=303)

        add_to_cart(
            request,
            produto.id,
            produto.name,
            float(produto.price),
            int(qty),
        )

        flash(request, "Produto adicionado ao carrinho.", "ok")

        return RedirectResponse(f"/loja/{empresa_id}", status_code=303)

    finally:
        db.close()
