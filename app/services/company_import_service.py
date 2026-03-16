from sqlalchemy.orm import Session

from app.models.company import Company


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def import_external_company(db: Session, data: dict) -> Company | None:
    name = _safe_text(data.get("name"))
    city = _safe_text(data.get("city"))
    state = _safe_text(data.get("state"))
    address = _safe_text(data.get("address"))
    phone = _safe_text(data.get("phone"))
    latitude = _safe_text(data.get("latitude"))
    longitude = _safe_text(data.get("longitude"))
    map_link = _safe_text(data.get("map_link"))
    description = _safe_text(data.get("description"))
    category = _safe_text(data.get("category"))

    if not name:
        return None

    query = db.query(Company).filter(Company.name == name)

    if city:
        query = query.filter(Company.city == city)

    if state:
        query = query.filter(Company.state == state)

    company = query.first()

    if company:
        updated = False

        if not company.address and address:
            company.address = address
            updated = True

        if not company.phone and phone:
            company.phone = phone
            updated = True

        if not company.latitude and latitude:
            company.latitude = latitude
            updated = True

        if not company.longitude and longitude:
            company.longitude = longitude
            updated = True

        if not company.map_link and map_link:
            company.map_link = map_link
            updated = True

        if not company.description and description:
            company.description = description
            updated = True

        if not company.specialties and category:
            company.specialties = category
            updated = True

        if updated:
            db.add(company)
            db.commit()
            db.refresh(company)

        return company

    company = Company(
        name=name,
        email="importado@radarlocal.local",
        phone=phone or None,
        city=city or None,
        state=state or None,
        address=address or None,
        latitude=latitude or None,
        longitude=longitude or None,
        map_link=map_link or None,
        description=description or "Empresa importada automaticamente pelo RADAR LOCAL.",
        specialties=category or None,
        status="approved",
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return company
