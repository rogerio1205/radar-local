from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.auth_service import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/users")
def api_users(request: Request):
    user = get_current_user(request)
    if not user:
        return {"error": "not authenticated"}

    db: Session = SessionLocal()
    try:
        users = db.query(User).all()
        return [{"id": u.id, "name": u.name, "email": u.email, "region": u.region} for u in users]
    finally:
        db.close()