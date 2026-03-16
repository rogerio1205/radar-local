import os
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.db.session import SessionLocal
from app.models.user import User


def require_login(request: Request, next_url: str | None = None):
    """
    Exige usuário logado.
    """
    user_id = request.session.get("user_id")

    if not user_id:
        target = next_url or request.url.path
        return RedirectResponse(url=f"/login?next={target}", status_code=303)

    return None


def _is_user_admin(user: User) -> bool:
    is_admin = False

    if hasattr(user, "is_admin"):
        is_admin = bool(getattr(user, "is_admin", False))

    if not is_admin and hasattr(user, "role"):
        is_admin = getattr(user, "role", None) == "admin"

    if not is_admin and hasattr(user, "roles") and user.roles:
        for user_role in user.roles:
            role_obj = getattr(user_role, "role", None)
            role_name = getattr(role_obj, "name", None)

            if role_name == "admin":
                is_admin = True
                break

    if not is_admin:
        admins = os.getenv("ADMIN_EMAILS", "")

        if admins:
            allowed = [e.strip().lower() for e in admins.split(",") if e.strip()]
            email = getattr(user, "email", "").strip().lower()

            if email in allowed:
                is_admin = True

    return is_admin


def require_admin(request: Request, next_url: str | None = None):
    """
    Exige usuário logado e com permissão de admin.
    """

    r = require_login(request, next_url=next_url)
    if r:
        return r

    user_id = request.session.get("user_id")

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()

        if not user:
            request.session.pop("user_id", None)
            return RedirectResponse(url="/login", status_code=303)

        if not _is_user_admin(user):
            request.session.pop("user_id", None)
            return RedirectResponse(url="/admin-login", status_code=303)

        return None

    finally:
        db.close()