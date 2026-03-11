from sqlalchemy.orm import Session
from sqlalchemy import text


def get_user_company_id(db: Session, user_id: int) -> int | None:
    row = db.execute(
        text("SELECT company_id FROM company_users WHERE user_id = :uid LIMIT 1"),
        {"uid": int(user_id)},
    ).fetchone()

    if not row:
        return None
    return int(row[0])


def is_user_company_owner(db: Session, user_id: int, company_id: int) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM company_users
            WHERE user_id = :uid AND company_id = :cid AND role IN ('owner','staff')
            LIMIT 1
            """
        ),
        {"uid": int(user_id), "cid": int(company_id)},
    ).fetchone()
    return bool(row)