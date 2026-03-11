from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.flash import flash
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.product import Product
from app.services.cart_service import add_to_cart

router = APIRouter(tags=["store-public"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/loja/{empresa_id}", response_class=HTMLResponse)
def public_store_page(request: Request, empresa_id: int):
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
            "loja_publica.html",
            {
                "empresa": empresa,
                "produtos": produtos,
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

        add_to_cart(request, produto.id, produto.name, float(produto.price), int(qty))
        flash(request, "Produto adicionado ao carrinho.", "ok")
        return RedirectResponse(f"/loja/{empresa_id}", status_code=303)

    finally:
        db.close()