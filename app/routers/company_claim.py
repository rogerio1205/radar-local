from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.flash import flash
from app.db.session import SessionLocal
from app.models.company import Company
from app.services.auth_service import get_current_user

router = APIRouter(tags=["company-claim"])


@router.get("/claim-company/{company_id}")
def claim_company(request: Request, company_id: int):
    db: Session = SessionLocal()

    try:
        company = db.query(Company).filter(Company.id == int(company_id)).first()

        if not company:
            flash(request, "Empresa não encontrada.", "error")
            return RedirectResponse("/mapa", status_code=303)

        user = get_current_user(request)

        target = f"/empresa/cadastrar?company_id={company.id}"

        if not user:
            flash(request, "Faça login para assumir esta empresa.", "error")
            return RedirectResponse(f"/login?next={target}", status_code=303)

        return RedirectResponse(target, status_code=303)

    finally:
        db.close()