from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import bcrypt

from app.core.flash import flash
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(tags=["company"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def ensure_company_users_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS company_users (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'owner'
            )
            """
        )
    )
    db.commit()


@router.get("/empresa/comecar")
def company_start(request: Request):
    flash(
        request,
        "Primeiro procure sua empresa no mapa. Quando localizar, clique em 'Sou dono desta empresa' para assumir o painel com os dados já preenchidos.",
        "ok",
    )
    return RedirectResponse("/mapa", status_code=303)


@router.get("/empresa/cadastrar", response_class=HTMLResponse)
def company_register_page(
    request: Request,
    company_id: int | None = None,
):
    db: Session = SessionLocal()

    try:
        company = None

        if company_id:
            company = db.query(Company).filter(Company.id == int(company_id)).first()

        return tpl(
            request,
            "company_register.html",
            {
                "company": company,
                "current_user": get_current_user(request),
            },
        )

    finally:
        db.close()


@router.post("/empresa/cadastrar")
def company_register(
    request: Request,
    company_id: int = Form(None),
    owner_name: str = Form(""),
    password: str = Form(""),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    instagram: str = Form(""),
    description: str = Form(""),
):
    db: Session = SessionLocal()

    try:
        ensure_company_users_table(db)

        user = get_current_user(request)

        email = _safe_text(email).lower()
        owner_name = _safe_text(owner_name)
        name = _safe_text(name)
        phone = _safe_text(phone)
        address = _safe_text(address)
        website = _safe_text(website)
        instagram = _safe_text(instagram)
        description = _safe_text(description)

        if not name:
            flash(request, "Informe o nome da empresa.", "error")
            return RedirectResponse("/empresa/cadastrar", status_code=303)

        if not email:
            flash(request, "Informe o email de contato.", "error")
            return RedirectResponse("/empresa/cadastrar", status_code=303)

        if not user:
            if not owner_name:
                flash(request, "Informe seu nome para criar o acesso.", "error")
                redirect_to = "/empresa/cadastrar"
                if company_id:
                    redirect_to += f"?company_id={company_id}"
                return RedirectResponse(redirect_to, status_code=303)

            if not password or len(password) < 4:
                flash(request, "Crie uma senha com pelo menos 4 caracteres.", "error")
                redirect_to = "/empresa/cadastrar"
                if company_id:
                    redirect_to += f"?company_id={company_id}"
                return RedirectResponse(redirect_to, status_code=303)

            existing_user = db.query(User).filter(User.email == email).first()

            if existing_user:
                flash(
                    request,
                    "Já existe uma conta com esse email. Faça login para assumir a empresa.",
                    "error",
                )
                redirect_target = f"/empresa/cadastrar?company_id={company_id}" if company_id else "/empresa/cadastrar"
                return RedirectResponse(f"/login?next={redirect_target}", status_code=303)

            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            user = User(
                name=owner_name,
                email=email,
                region="RADAR LOCAL",
                password_hash=hashed,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            request.session["user_id"] = user.id

        existing_link = db.execute(
            text("SELECT 1 FROM company_users WHERE user_id = :uid LIMIT 1"),
            {"uid": int(user.id)},
        ).fetchone()

        if existing_link and not company_id:
            flash(request, "Você já possui uma empresa vinculada.", "error")
            return RedirectResponse("/empresa/dashboard", status_code=303)

        if company_id:
            company = db.query(Company).filter(Company.id == int(company_id)).first()

            if not company:
                flash(request, "Empresa não encontrada.", "error")
                return RedirectResponse("/empresa/cadastrar", status_code=303)

            company.name = name
            company.email = email
            company.phone = phone or None
            company.address = address or None
            company.website = website or None
            company.instagram = instagram or None
            company.description = description or company.description
            company.status = "pending"

            db.commit()

            already_owner = db.execute(
                text(
                    """
                    SELECT 1
                    FROM company_users
                    WHERE company_id = :cid AND user_id = :uid
                    LIMIT 1
                    """
                ),
                {"cid": int(company.id), "uid": int(user.id)},
            ).fetchone()

            if not already_owner:
                db.execute(
                    text(
                        """
                        INSERT INTO company_users (company_id, user_id, role)
                        VALUES (:cid, :uid, 'owner')
                        """
                    ),
                    {"cid": int(company.id), "uid": int(user.id)},
                )
                db.commit()

            flash(request, "Empresa vinculada à sua conta com sucesso.", "ok")
            return RedirectResponse("/empresa/dashboard", status_code=303)

        company = Company(
            name=name,
            email=email,
            phone=phone or None,
            address=address or None,
            website=website or None,
            instagram=instagram or None,
            description=description or None,
            status="pending",
        )

        db.add(company)
        db.commit()
        db.refresh(company)

        db.execute(
            text(
                """
                INSERT INTO company_users (company_id, user_id, role)
                VALUES (:cid, :uid, 'owner')
                """
            ),
            {"cid": int(company.id), "uid": int(user.id)},
        )
        db.commit()

        flash(request, "Empresa cadastrada com sucesso.", "ok")
        return RedirectResponse("/empresa/dashboard", status_code=303)

    except IntegrityError:
        db.rollback()
        flash(request, "Não foi possível concluir o cadastro. Verifique os dados informados.", "error")
        redirect_to = "/empresa/cadastrar"
        if company_id:
            redirect_to += f"?company_id={company_id}"
        return RedirectResponse(redirect_to, status_code=303)

    except Exception:
        db.rollback()
        flash(request, "Erro interno ao concluir o cadastro da empresa.", "error")
        redirect_to = "/empresa/cadastrar"
        if company_id:
            redirect_to += f"?company_id={company_id}"
        return RedirectResponse(redirect_to, status_code=303)

    finally:
        db.close()