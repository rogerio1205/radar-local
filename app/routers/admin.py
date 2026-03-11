from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.tpl import templates
from app.core.guards import require_admin
from app.core.flash import flash
from app.db.session import SessionLocal
from app.models.product import Product

from app.services.admin_service import (
    get_admin_dashboard_metrics,
    get_dashboard_daily_series,
    list_orders_admin,
    get_order_admin,
    update_order_status_admin,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------
# DASHBOARD
# ---------------------------

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_home(request: Request):
    guard = require_admin(request, next_url="/admin")
    if guard:
        return guard

    db: Session = SessionLocal()
    try:
        metrics = get_admin_dashboard_metrics(db)
        series_7 = get_dashboard_daily_series(db, days=7)
        series_30 = get_dashboard_daily_series(db, days=30)

        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "metrics": metrics,
                "series_7": series_7,
                "series_30": series_30,
            },
        )
    finally:
        db.close()


# ---------------------------
# PEDIDOS (ADMIN)
# ---------------------------

@router.get("/orders", response_class=HTMLResponse)
def admin_orders(request: Request, status: str | None = Query(default=None)):
    guard = require_admin(request, next_url="/admin/orders")
    if guard:
        return guard

    db: Session = SessionLocal()
    try:
        orders = list_orders_admin(db, status=status)
        return templates.TemplateResponse(
            "admin_orders.html",
            {"request": request, "orders": orders, "status": status},
        )
    finally:
        db.close()


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def admin_order_detail(request: Request, order_id: int):
    guard = require_admin(request, next_url=f"/admin/orders/{order_id}")
    if guard:
        return guard

    db: Session = SessionLocal()
    try:
        order = get_order_admin(db, order_id)
        if not order:
            flash(request, "Pedido não encontrado.", "error")
            return RedirectResponse("/admin/orders", status_code=303)

        return templates.TemplateResponse(
            "admin_order_detail.html",
            {"request": request, "order": order},
        )
    finally:
        db.close()


@router.post("/orders/{order_id}/status")
def admin_order_update_status(request: Request, order_id: int, status: str = Form(...)):
    guard = require_admin(request, next_url=f"/admin/orders/{order_id}")
    if guard:
        return guard

    allowed = {"novo", "pago", "enviado", "cancelado"}
    if status not in allowed:
        flash(request, "Status inválido.", "error")
        return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)

    db: Session = SessionLocal()
    try:
        ok = update_order_status_admin(db, order_id, status)
        if not ok:
            flash(request, "Pedido não encontrado.", "error")
            return RedirectResponse("/admin/orders", status_code=303)
    finally:
        db.close()

    flash(request, "Status atualizado.", "ok")
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


# ---------------------------
# PRODUTOS (ADMIN)
# ---------------------------

@router.get("/products", response_class=HTMLResponse)
def admin_products(request: Request):
    guard = require_admin(request, next_url="/admin/products")
    if guard:
        return guard

    db: Session = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id.desc()).all()
        return templates.TemplateResponse(
            "admin_products.html",
            {"request": request, "products": products},
        )
    finally:
        db.close()


@router.post("/products/create")
def admin_products_create(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
):
    guard = require_admin(request, next_url="/admin/products")
    if guard:
        return guard

    db: Session = SessionLocal()
    try:
        p = Product(name=name, price=price, stock=stock)
        db.add(p)
        db.commit()
        flash(request, "Produto criado.", "ok")
        return RedirectResponse("/admin/products", status_code=303)
    finally:
        db.close()


@router.post("/products/{product_id}/stock")
def admin_products_update_stock(
    request: Request,
    product_id: int,
    stock: int = Form(...),
):
    guard = require_admin(request, next_url="/admin/products")
    if guard:
        return guard

    db: Session = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if p:
            p.stock = stock
            db.commit()
            flash(request, "Estoque atualizado.", "ok")
        else:
            flash(request, "Produto não encontrado.", "error")
        return RedirectResponse("/admin/products", status_code=303)
    finally:
        db.close()