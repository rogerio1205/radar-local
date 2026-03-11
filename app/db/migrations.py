from sqlalchemy import text
from app.db.session import engine


def _has_column(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    cols = {r[1] for r in rows}  # r[1] = column name
    return column in cols


def run_migrations() -> None:
    """
    Migração leve para SQLite (idempotente).
    - cria companies
    - cria company_users
    - adiciona company_id em products (se não existir)
    """
    with engine.begin() as conn:
        # companies
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    legal_name VARCHAR NULL,
                    cnpj VARCHAR NULL,
                    email VARCHAR NOT NULL,
                    phone VARCHAR NULL,
                    address VARCHAR NULL,
                    website VARCHAR NULL,
                    instagram VARCHAR NULL,
                    description VARCHAR NULL,
                    status VARCHAR NOT NULL DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        # company_users (preparado para multi-usuário por empresa)
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS company_users (
                    id INTEGER PRIMARY KEY,
                    company_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role VARCHAR NOT NULL DEFAULT 'owner',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, user_id),
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
                )
                """
            )
        )

        # products.company_id
        # (só adiciona se não existir)
        try:
            if not _has_column(conn, "products", "company_id"):
                conn.execute(text("ALTER TABLE products ADD COLUMN company_id INTEGER NULL"))
        except Exception:
            # Se products não existir ainda, não faz nada
            pass