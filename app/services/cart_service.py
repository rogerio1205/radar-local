from fastapi import Request
from typing import List, Dict

SESSION_CART_KEY = "cart_items"

def get_cart(request: Request) -> List[Dict]:
    cart = request.session.get(SESSION_CART_KEY)
    if not isinstance(cart, list):
        cart = []
    return cart

def save_cart(request: Request, cart: List[Dict]) -> None:
    request.session[SESSION_CART_KEY] = cart

def add_to_cart(request: Request, product_id: int, name: str, price: float, qty: int) -> None:
    qty = int(qty)
    if qty < 1:
        qty = 1

    cart = get_cart(request)

    for item in cart:
        if int(item.get("product_id")) == int(product_id):
            item["qty"] = int(item.get("qty", 0)) + qty
            save_cart(request, cart)
            return

    cart.append(
        {
            "product_id": int(product_id),
            "name": name,
            "price": float(price),
            "qty": qty,
        }
    )
    save_cart(request, cart)

def cart_total(cart: List[Dict]) -> float:
    return sum(float(i.get("price", 0)) * int(i.get("qty", 1)) for i in cart)

def clear_cart(request: Request) -> None:
    save_cart(request, [])