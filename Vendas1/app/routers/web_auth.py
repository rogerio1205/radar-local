from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import bcrypt

from app.db.session import SessionLocal
from app.models.user import User
from app.core.flash import flash
from app.services.seed_service import ensure_rbac_seed, ensure_first_user_is_admin

router = APIRouter()

def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    next_url = request.query_params.get("next", "/")
    return tpl(request, "login.html", {"next_url": next_url})

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/"),
):
    db: Session = SessionLocal()
    try:
        email = (email or "").strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            flash(request, "Email ou senha inválidos.", "error")
            return tpl(request, "login.html", {"next_url": next_url}, status_code=400)

        ok = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
        if not ok:
            flash(request, "Senha incorreta.", "error")
            return tpl(request, "login.html", {"next_url": next_url}, status_code=400)

        request.session["user_id"] = user.id
        flash(request, "Bem-vindo! Login realizado com sucesso.", "ok")

        if not next_url.startswith("/"):
            next_url = "/"
        return RedirectResponse(next_url or "/", status_code=303)
    finally:
        db.close()

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Você saiu da sua conta.", "ok")
    return RedirectResponse("/login", status_code=303)

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return tpl(request, "register.html")

@router.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    region: str = Form(...),
    password: str = Form(...),
):
    db: Session = SessionLocal()
    try:
        # garante RBAC seed (roles/perms) antes de criar usuário
        ensure_rbac_seed(db)

        email = (email or "").strip().lower()
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        new_user = User(
            name=name.strip(),
            email=email,
            region=region.strip(),
            password_hash=hashed,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # ✅ primeiro usuário cadastrado vira admin
        ensure_first_user_is_admin(db, new_user.id)

        flash(request, "Conta criada! Faça login.", "ok")
        return RedirectResponse("/login", status_code=303)

    except IntegrityError:
        db.rollback()
        flash(request, "Esse email já está cadastrado. Use outro ou faça login.", "error")
        return tpl(request, "register.html", status_code=400)

    finally:
        db.close()