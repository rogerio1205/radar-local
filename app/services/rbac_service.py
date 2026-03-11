from fastapi import Request, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.auth_service import get_current_user


def has_permission(user_id: int, permission_code: str) -> bool:
    db: Session = SessionLocal()
    try:
        row = db.execute(
            text(
                """
                SELECT 1
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                JOIN user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = :uid AND p.code = :pc
                LIMIT 1
                """
            ),
            {"uid": int(user_id), "pc": permission_code},
        ).fetchone()
        return bool(row)
    finally:
        db.close()


def require_permission(permission_code: str):
    def dep(request: Request):
        user = get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": f"/login?next={request.url.path}"},
            )

        if not has_permission(int(user.id), permission_code):
            raise HTTPException(status_code=403, detail="Sem permissão")

        return True

    return dep