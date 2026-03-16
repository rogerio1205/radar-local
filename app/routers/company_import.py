from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.flash import flash
from app.services.company_import_service import import_external_company
from app.services.auth_service import get_current_user

router = APIRouter(tags=["company-import"])


@router.get("/import-company")
def import_company(
    request: Request,
    name: str = "",
    city: str = "",
    state: str = "",
    address: str = "",
    phone: str = "",
    latitude: str = "",
    longitude: str = "",
    map_link: str = "",
    description: str = "",
    category: str = "",
):
    db: Session = SessionLocal()

    try:
        company = import_external_company(
            db,
            {
                "name": name,
                "city": city,
                "state": state,
                "address": address,
                "phone": phone,
                "latitude": latitude,
                "longitude": longitude,
                "map_link": map_link,
                "description": description,
                "category": category,
            },
        )

        if not company:
            flash(request, "Não foi possível importar a empresa.", "error")
            return RedirectResponse("/mapa", status_code=303)

        user = get_current_user(request)

        if not user:
            flash(request, "Faça login para continuar.", "error")
            return RedirectResponse(f"/login?next=/loja/{company.id}", status_code=303)

        flash(request, "Empresa importada com sucesso para o RADAR LOCAL.", "ok")
        return RedirectResponse(f"/loja/{company.id}", status_code=303)

    except Exception:
        flash(request, "Erro ao importar a empresa para o portal.", "error")
        return RedirectResponse("/mapa", status_code=303)

    finally:
        db.close()
