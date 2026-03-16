from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.product import Product

from app.services.geocoding_service import geocode_region
from app.services.places_service import search_places

router = APIRouter(tags=["map-view"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_google_maps_link(name: str = "", address: str = "", city: str = "", state: str = "") -> str:
    query_parts = [name, address, city, state]
    query = ", ".join([_safe_text(x) for x in query_parts if _safe_text(x)])

    if not query:
        query = "Brasil"

    return f"https://www.google.com/maps/search/?api=1&query={urlencode({'q': query})[2:]}"


def _build_import_url(empresa: dict) -> str:
    params = {
        "name": _safe_text(empresa.get("name")),
        "city": _safe_text(empresa.get("city")),
        "state": _safe_text(empresa.get("state")),
        "address": _safe_text(empresa.get("address")),
        "phone": _safe_text(empresa.get("phone")),
        "latitude": _safe_text(empresa.get("latitude")),
        "longitude": _safe_text(empresa.get("longitude")),
        "map_link": _safe_text(empresa.get("map_link")),
        "description": _safe_text(empresa.get("description")),
        "category": _safe_text(empresa.get("category")),
    }

    clean_params = {k: v for k, v in params.items() if v}
    return f"/import-company?{urlencode(clean_params)}"


@router.get("/mapa", response_class=HTMLResponse)
def mapa_page(request: Request):
    pais = _safe_text(request.query_params.get("pais"))
    estado = _safe_text(request.query_params.get("estado"))
    cidade = _safe_text(request.query_params.get("cidade"))
    bairro = _safe_text(request.query_params.get("bairro"))
    q = _safe_text(request.query_params.get("q"))

    map_center = geocode_region(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    db: Session = SessionLocal()
    try:
        lojas_internas = []
        empresas_externas = []
        pontos = []

        if q:
            query = (
                db.query(Company)
                .outerjoin(Product, Product.company_id == Company.id)
                .filter(Company.status == "approved")
            )

            if pais:
                query = query.filter(Company.country.ilike(f"%{pais}%"))

            if estado:
                query = query.filter(Company.state.ilike(f"%{estado}%"))

            if cidade:
                query = query.filter(Company.city.ilike(f"%{cidade}%"))

            if bairro:
                query = query.filter(Company.neighborhood.ilike(f"%{bairro}%"))

            query = query.filter(
                or_(
                    Company.name.ilike(f"%{q}%"),
                    Company.description.ilike(f"%{q}%"),
                    Company.specialties.ilike(f"%{q}%"),
                    Product.name.ilike(f"%{q}%"),
                    Product.category.ilike(f"%{q}%"),
                )
            )

            lojas_internas = query.distinct().order_by(Company.id.desc()).all()

            for loja in lojas_internas:
                lat = _safe_text(loja.latitude)
                lng = _safe_text(loja.longitude)
                map_link = _safe_text(loja.map_link) or _build_google_maps_link(
                    name=loja.name,
                    address=loja.address,
                    city=loja.city,
                    state=loja.state,
                )

                loja.map_link = map_link

                if lat and lng:
                    pontos.append(
                        {
                            "id": loja.id,
                            "source": "portal",
                            "name": loja.name or "",
                            "city": loja.city or "",
                            "state": loja.state or "",
                            "latitude": lat,
                            "longitude": lng,
                            "url": f"/loja/{loja.id}",
                            "map_link": map_link,
                            "import_url": "",
                        }
                    )

            empresas_externas_encontradas = search_places(
                pais=pais,
                estado=estado,
                cidade=cidade,
                bairro=bairro,
                q=q,
                limit=30,
            )

            empresas_externas_tratadas = []

            for empresa in empresas_externas_encontradas:
                empresa_map_link = _safe_text(empresa.get("map_link")) or _build_google_maps_link(
                    name=empresa.get("name"),
                    address=empresa.get("address"),
                    city=empresa.get("city"),
                    state=empresa.get("state"),
                )

                empresa["map_link"] = empresa_map_link
                empresa["import_url"] = _build_import_url(empresa)
                empresas_externas_tratadas.append(empresa)

                lat = _safe_text(empresa.get("latitude"))
                lng = _safe_text(empresa.get("longitude"))

                if lat and lng:
                    pontos.append(
                        {
                            "id": empresa.get("external_id", ""),
                            "source": "externa",
                            "name": empresa.get("name", ""),
                            "city": empresa.get("city", ""),
                            "state": empresa.get("state", ""),
                            "latitude": lat,
                            "longitude": lng,
                            "url": empresa["import_url"],
                            "map_link": empresa_map_link,
                            "import_url": empresa["import_url"],
                        }
                    )

            empresas_externas = empresas_externas_tratadas

        return tpl(
            request,
            "mapa.html",
            {
                "lojas": lojas_internas,
                "empresas_externas": empresas_externas,
                "pontos": pontos,
                "map_center": map_center,
                "filtros": {
                    "pais": pais,
                    "estado": estado,
                    "cidade": cidade,
                    "bairro": bairro,
                    "q": q,
                },
                "search_ready": True if q else False,
            },
        )

    except Exception:
        return tpl(
            request,
            "mapa.html",
            {
                "lojas": [],
                "empresas_externas": [],
                "pontos": [],
                "map_center": map_center,
                "filtros": {
                    "pais": pais,
                    "estado": estado,
                    "cidade": cidade,
                    "bairro": bairro,
                    "q": q,
                },
                "search_ready": True if q else False,
                "mapa_error": "Não foi possível carregar o mapa no momento.",
            },
            status_code=500,
        )

    finally:
        db.close()
