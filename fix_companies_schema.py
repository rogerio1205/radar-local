from sqlalchemy import inspect, text
from app.db.session import engine


def add_column_if_missing(conn, columns, name, ddl):
    if name not in columns:
        print(f"Adicionando coluna: {name}")
        conn.execute(text(ddl))


def main():
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    if "companies" not in tables:
        print("Tabela 'companies' não existe.")
        return

    cols = {c["name"] for c in inspector.get_columns("companies")}
    print("Colunas atuais em companies:", sorted(cols))

    with engine.begin() as conn:
        add_column_if_missing(conn, cols, "whatsapp", "ALTER TABLE companies ADD COLUMN whatsapp VARCHAR")
        add_column_if_missing(conn, cols, "country", "ALTER TABLE companies ADD COLUMN country VARCHAR")
        add_column_if_missing(conn, cols, "state", "ALTER TABLE companies ADD COLUMN state VARCHAR")
        add_column_if_missing(conn, cols, "city", "ALTER TABLE companies ADD COLUMN city VARCHAR")
        add_column_if_missing(conn, cols, "neighborhood", "ALTER TABLE companies ADD COLUMN neighborhood VARCHAR")
        add_column_if_missing(conn, cols, "map_link", "ALTER TABLE companies ADD COLUMN map_link VARCHAR")
        add_column_if_missing(conn, cols, "pix_key", "ALTER TABLE companies ADD COLUMN pix_key VARCHAR")
        add_column_if_missing(conn, cols, "latitude", "ALTER TABLE companies ADD COLUMN latitude VARCHAR")
        add_column_if_missing(conn, cols, "longitude", "ALTER TABLE companies ADD COLUMN longitude VARCHAR")
        add_column_if_missing(conn, cols, "specialties", "ALTER TABLE companies ADD COLUMN specialties VARCHAR")

    inspector = inspect(engine)
    cols_after = {c["name"] for c in inspector.get_columns("companies")}
    print("Colunas finais em companies:", sorted(cols_after))
    print("OK - schema de companies corrigido.")


if __name__ == "__main__":
    main()