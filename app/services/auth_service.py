from fastapi import Request
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User


def get_current_user(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    db: Session = SessionLocal()

    try:
        return db.query(User).filter(User.id == int(user_id)).first()
    finally:
        db.close()