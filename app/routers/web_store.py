from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.guards import require_login
from app.core.flash import flash
from app.services.auth_service import get_current_user
from app.services.cart_service import get_cart, add_to_cart, cart_total, clear_cart
from app.services.order_service import validate_and_price_items, create_order_from_items

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.order import Order

router = APIRouter()


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _safe_user_value(user, field_names: list[str], default: str = "") -> str:
    for field in field_names:
        value = getattr(user, field, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse("/mapa", status_code=303)


@router.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request):
    cart = get_cart(request)
    total = cart_total(cart)

    user = get_current_user(request)

    checkout_data = {
        "customer_name": "",
        "customer_phone": "",
        "customer_address": "",
    }

    if user:
        checkout_data["customer_name"] = _safe_user_value(
            user,
            ["name", "full_name", "username"],
            "",
        )
        checkout_data["customer_phone"] = _safe_user_value(
            user,
            ["phone", "telephone", "mobile"],
            "",
        )
        checkout_data["customer_address"] = _safe_user_value(
            user,
            ["address", "street_address", "full_address"],
            "",
        )

    return tpl(
        request,
        "cart.html",
        {
            "items": cart,
            "total": total,
            "checkout_data": checkout_data,
            "user_logged": bool(user),
        },
    )


@router.post("/cart/add")
def cart_add(request: Request, product_id: int = Form(...), qty: int = Form(...)):
    db: Session = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == int(product_id)).first()
    finally:
        db.close()

    if not product:
        flash(request, "Produto não encontrado.", "error")
        return RedirectResponse("/mapa", status_code=303)

    if not getattr(product, "active", True):
        flash(request, "Produto está inativo.", "error")
        return RedirectResponse("/mapa", status_code=303)

    qty = max(1, int(qty))

    add_to_cart(request, product.id, product.name, float(product.price), qty)
    flash(request, "Produto adicionado ao carrinho.", "ok")
    return RedirectResponse("/cart", status_code=303)


@router.post("/cart/checkout")
def cart_checkout(
    request: Request,
    customer_name: str = Form(""),
    customer_phone: str = Form(""),
    customer_address: str = Form(""),
    payment_method: str = Form(...),
):
    guard = require_login(request, next_url="/cart")
    if guard:
        return guard

    cart = get_cart(request)
    if not cart:
        flash(request, "Seu carrinho está vazio.", "error")
        return RedirectResponse("/cart", status_code=303)

    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/cart", status_code=303)

    customer_name = customer_name.strip() or _safe_user_value(
        user,
        ["name", "full_name", "username"],
        "",
    )
    customer_phone = customer_phone.strip() or _safe_user_value(
        user,
        ["phone", "telephone", "mobile"],
        "",
    )
    customer_address = customer_address.strip() or _safe_user_value(
        user,
        ["address", "street_address", "full_address"],
        "",
    )

    if not customer_name:
        flash(request, "Informe o nome do cliente.", "error")
        return RedirectResponse("/cart", status_code=303)

    if not customer_phone:
        flash(request, "Informe o telefone do cliente.", "error")
        return RedirectResponse("/cart", status_code=303)

    if not customer_address:
        flash(request, "Informe o endereço do cliente.", "error")
        return RedirectResponse("/cart", status_code=303)

    db: Session = SessionLocal()
    try:
        _, items = validate_and_price_items(db, cart)

        order = create_order_from_items(
            db=db,
            user_id=user.id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            payment_method=payment_method,
            items=items,
            status="novo",
        )

        clear_cart(request)
        flash(request, "Pedido criado com sucesso!", "ok")

        if payment_method == "pix":
            return RedirectResponse(f"/payment/pix/{order.id}", status_code=303)

        return RedirectResponse("/meus-pedidos", status_code=303)

    except ValueError as ve:
        db.rollback()
        flash(request, str(ve), "error")
        return RedirectResponse("/cart", status_code=303)

    except Exception:
        db.rollback()
        flash(request, "Erro interno ao finalizar o pedido.", "error")
        return RedirectResponse("/cart", status_code=303)

    finally:
        db.close()


@router.get("/meus-pedidos", response_class=HTMLResponse)
def meus_pedidos(request: Request):
    guard = require_login(request, next_url="/meus-pedidos")
    if guard:
        return guard

    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/meus-pedidos", status_code=303)

    db: Session = SessionLocal()
    try:
        orders_list = (
            db.query(Order)
            .filter(Order.user_id == user.id)
            .order_by(Order.id.desc())
            .all()
        )
    finally:
        db.close()

    return tpl(request, "meus_pedidos.html", {"orders": orders_list})