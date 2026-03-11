import os
from io import BytesIO

import qrcode
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from sqlalchemy.orm import Session

from app.core.guards import require_login
from app.core.flash import flash
from app.db.session import SessionLocal
from app.services.auth_service import get_current_user
from app.models.order import Order

router = APIRouter(prefix="/payment", tags=["payment"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def build_pix_payload(order: Order) -> str:
    # MVP: payload simples para testes
    # Depois podemos trocar por EMVCo PIX real
    pix_key = os.getenv("PIX_KEY", "pix@teste.com")
    return f"PIX|ORDER={order.id}|TOTAL={order.total:.2f}|NAME={order.customer_name}|KEY={pix_key}"


@router.get("/pix/{order_id}", response_class=HTMLResponse)
def pix_payment_page(request: Request, order_id: int):
    guard = require_login(request, next_url=f"/payment/pix/{order_id}")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.id == int(order_id),
            Order.user_id == int(user.id)
        ).first()

        if not order:
            flash(request, "Pedido não encontrado.", "error")
            return RedirectResponse("/meus-pedidos", status_code=303)

        payload = build_pix_payload(order)

    finally:
        db.close()

    return tpl(request, "payment_pix.html", {"order": order, "pix_payload": payload})


@router.get("/pix/{order_id}/qr")
def pix_qr(request: Request, order_id: int):
    guard = require_login(request, next_url=f"/payment/pix/{order_id}")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.id == int(order_id),
            Order.user_id == int(user.id)
        ).first()

        if not order:
            return Response(status_code=404)

        payload = build_pix_payload(order)

    finally:
        db.close()

    qr = qrcode.QRCode(box_size=10, border=5)
    qr.add_data(payload)
    qr.make()

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")

    return Response(buf.getvalue(), media_type="image/png")


@router.post("/pix/{order_id}/confirm")
def pix_confirm(request: Request, order_id: int):
    guard = require_login(request, next_url=f"/payment/pix/{order_id}")
    if guard:
        return guard

    user = get_current_user(request)

    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.id == int(order_id),
            Order.user_id == int(user.id)
        ).first()

        if not order:
            flash(request, "Pedido não encontrado.", "error")
            return RedirectResponse("/meus-pedidos", status_code=303)

        order.payment_status = "pago"
        order.status = "pago"
        db.commit()

    finally:
        db.close()

    flash(request, "Pagamento confirmado.", "ok")
    return RedirectResponse("/meus-pedidos", status_code=303)