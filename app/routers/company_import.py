from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.flash import flash
from app.db.session import SessionLocal
from app.services.auth_service import get_current_user
from app.services.company_import_service import import_external_company

router = APIRouter(tags=["company-import"])


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_self_url(
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
    website: str = "",
    country: str = "",
    neighborhood: str = "",
    source: str = "",
    external_id: str = "",
    next_action: str = "",
) -> str:
    params = {
        "name": _safe_text(name),
        "city": _safe_text(city),
        "state": _safe_text(state),
        "address": _safe_text(address),
        "phone": _safe_text(phone),
        "latitude": _safe_text(latitude),
        "longitude": _safe_text(longitude),
        "map_link": _safe_text(map_link),
        "description": _safe_text(description),
        "category": _safe_text(category),
        "website": _safe_text(website),
        "country": _safe_text(country),
        "neighborhood": _safe_text(neighborhood),
        "source": _safe_text(source),
        "external_id": _safe_text(external_id),
        "next_action": _safe_text(next_action) or "store",
    }

    clean_params = {k: v for k, v in params.items() if v}
    return f"/import-company?{urlencode(clean_params)}"


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
    website: str = "",
    country: str = "",
    neighborhood: str = "",
    source: str = "",
    external_id: str = "",
    next_action: str = "store",
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
                "website": website,
                "country": country,
                "neighborhood": neighborhood,
                "source": source,
                "external_id": external_id,
            },
        )

        if not company:
            flash(request, "Não foi possível importar a empresa.", "error")
            return RedirectResponse("/mapa", status_code=303)

        user = get_current_user(request)
        action = _safe_text(next_action).lower() or "store"

        if action == "claim":
            if not user:
                flash(request, "Faça login para assumir esta empresa.", "error")
                next_url = _build_self_url(
                    name=name,
                    city=city,
                    state=state,
                    address=address,
                    phone=phone,
                    latitude=latitude,
                    longitude=longitude,
                    map_link=map_link,
                    description=description,
                    category=category,
                    website=website,
                    country=country,
                    neighborhood=neighborhood,
                    source=source,
                    external_id=external_id,
                    next_action="claim",
                )
                return RedirectResponse(f"/login?next={next_url}", status_code=303)

            flash(request, "Empresa importada com sucesso. Agora complete o vínculo como dono.", "ok")
            return RedirectResponse(f"/claim-company/{company.id}", status_code=303)

        flash(request, "Empresa importada com sucesso para o Rota Local.", "ok")
        return RedirectResponse(f"/loja/{company.id}", status_code=303)

    except Exception:
        flash(request, "Erro ao importar a empresa para o portal.", "error")
        return RedirectResponse("/mapa", status_code=303)

    finally:
        db.close()