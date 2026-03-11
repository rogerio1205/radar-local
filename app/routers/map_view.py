from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.product import Product

router = APIRouter(tags=["map-view"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/mapa", response_class=HTMLResponse)
def mapa_page(request: Request):
    pais = (request.query_params.get("pais") or "").strip()
    estado = (request.query_params.get("estado") or "").strip()
    cidade = (request.query_params.get("cidade") or "").strip()
    bairro = (request.query_params.get("bairro") or "").strip()
    q = (request.query_params.get("q") or "").strip()

    db: Session = SessionLocal()
    try:
        query = db.query(Company).outerjoin(Product, Product.company_id == Company.id).filter(Company.status == "approved")

        if pais and hasattr(Company, "country"):
            query = query.filter(Company.country.ilike(f"%{pais}%"))

        if estado and hasattr(Company, "state"):
            query = query.filter(Company.state.ilike(f"%{estado}%"))

        if cidade and hasattr(Company, "city"):
            query = query.filter(Company.city.ilike(f"%{cidade}%"))

        if bairro and hasattr(Company, "neighborhood"):
            query = query.filter(Company.neighborhood.ilike(f"%{bairro}%"))

        if q:
            query = query.filter(
                or_(
                    Company.name.ilike(f"%{q}%"),
                    Company.description.ilike(f"%{q}%"),
                    Company.specialties.ilike(f"%{q}%"),
                    Product.name.ilike(f"%{q}%"),
                    Product.category.ilike(f"%{q}%"),
                )
            )

        lojas = query.distinct().order_by(Company.id.desc()).all()

        pontos = []
        for loja in lojas:
            lat = (loja.latitude or "").strip() if loja.latitude else ""
            lng = (loja.longitude or "").strip() if loja.longitude else ""

            if lat and lng:
                pontos.append(
                    {
                        "id": loja.id,
                        "name": loja.name,
                        "city": loja.city or "",
                        "state": loja.state or "",
                        "latitude": lat,
                        "longitude": lng,
                    }
                )

        return tpl(
            request,
            "mapa.html",
            {
                "lojas": lojas,
                "pontos": pontos,
                "filtros": {
                    "pais": pais,
                    "estado": estado,
                    "cidade": cidade,
                    "bairro": bairro,
                    "q": q,
                },
            },
        )
    finally:
        db.close()