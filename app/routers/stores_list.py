from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.company import Company

router = APIRouter(tags=["stores-list"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


@router.get("/lojas", response_class=HTMLResponse)
def stores_list_page(request: Request):
    db: Session = SessionLocal()
    try:
        lojas = (
            db.query(Company)
            .filter(Company.status == "approved")
            .order_by(Company.id.desc())
            .all()
        )
        return tpl(
            request,
            "lojas.html",
            {
                "lojas": lojas,
            },
        )
    finally:
        db.close()