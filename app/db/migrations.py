from sqlalchemy import inspect, text

from app.db.session import engine


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    try:
        cols = inspector.get_columns(table_name)
    except Exception:
        return False

    names = {c.get("name") for c in cols}
    return column_name in names


def run_migrations() -> None:
    """
    Migração leve e idempotente para SQLite/PostgreSQL.
    - garante company_users
    - garante products.company_id
    """
    with engine.begin() as conn:
        inspector = inspect(conn)
        dialect = conn.dialect.name

        if not _table_exists(inspector, "company_users"):
            if dialect == "sqlite":
                conn.execute(
                    text(
                        """
                        CREATE TABLE company_users (
                            id INTEGER PRIMARY KEY,
                            company_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            role VARCHAR(50) NOT NULL DEFAULT 'owner',
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(company_id, user_id),
                            FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                    )
                )
            else:
                conn.execute(
                    text(
                        """
                        CREATE TABLE company_users (
                            id SERIAL PRIMARY KEY,
                            company_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            role VARCHAR(50) NOT NULL DEFAULT 'owner',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT uq_company_users_company_user UNIQUE (company_id, user_id),
                            CONSTRAINT fk_company_users_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                            CONSTRAINT fk_company_users_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                    )
                )

        inspector = inspect(conn)

        if _table_exists(inspector, "products") and not _has_column(inspector, "products", "company_id"):
            conn.execute(text("ALTER TABLE products ADD COLUMN company_id INTEGER NULL"))