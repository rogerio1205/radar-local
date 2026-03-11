from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.product import Product
from app.core.flash import flash
from app.services.rbac_service import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])

def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)

@router.get(
    "/products",
    response_class=HTMLResponse,
    dependencies=[Depends(require_permission("admin.products.manage"))],
)
def admin_products_page(request: Request):
    db: Session = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id.desc()).all()
    finally:
        db.close()

    return tpl(request, "admin_products.html", {"products": products})

@router.post(
    "/products",
    dependencies=[Depends(require_permission("admin.products.manage"))],
)
def admin_products_create(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category: str = Form(""),
    sku: str = Form(""),
    active: str = Form("on"),
):
    db: Session = SessionLocal()
    try:
        p = Product(
            name=name.strip(),
            price=float(price),
            stock=int(stock),
            category=(category.strip() or None),
            sku=(sku.strip() or None),
            active=(active == "on"),
        )
        db.add(p)
        db.commit()
    finally:
        db.close()

    flash(request, "Produto criado com sucesso.", "ok")
    return RedirectResponse("/admin/products", status_code=303)

@router.post(
    "/products/{product_id}/toggle",
    dependencies=[Depends(require_permission("admin.products.manage"))],
)
def admin_products_toggle(request: Request, product_id: int):
    db: Session = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == int(product_id)).first()
        if not p:
            flash(request, "Produto não encontrado.", "error")
            return RedirectResponse("/admin/products", status_code=303)

        p.active = not bool(p.active)
        db.commit()
    finally:
        db.close()

    flash(request, "Produto atualizado.", "ok")
    return RedirectResponse("/admin/products", status_code=303)