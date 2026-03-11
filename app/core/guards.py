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


def require_admin(request: Request, next_url: str | None = None):
    """
    Exige usuário logado e com permissão de admin.
    """

    # 1) verifica login
    r = require_login(request, next_url=next_url)
    if r:
        return r

    user_id = request.session.get("user_id")

    db = SessionLocal()

    try:

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            request.session.pop("user_id", None)
            return RedirectResponse(url="/login", status_code=303)

        # verificar admin
        is_admin = False

        if hasattr(user, "is_admin"):
            is_admin = bool(user.is_admin)

        if not is_admin and hasattr(user, "role"):
            is_admin = user.role == "admin"

        # lista de admins via variável de ambiente
        if not is_admin:
            admins = os.getenv("ADMIN_EMAILS", "")

            if admins:
                allowed = [e.strip().lower() for e in admins.split(",")]

                email = getattr(user, "email", "").lower()

                if email in allowed:
                    is_admin = True

        if not is_admin:
            return RedirectResponse(url="/", status_code=303)

        return None

    finally:
        db.close()