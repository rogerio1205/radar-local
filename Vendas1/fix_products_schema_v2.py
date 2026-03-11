from sqlalchemy import inspect, text
from app.db.session import engine


def add_column_if_missing(conn, columns, name, ddl):
    if name not in columns:
        print(f"Adicionando coluna: {name}")
        conn.execute(text(ddl))


def main():
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    if "products" not in tables:
        print("Tabela 'products' não existe.")
        return

    cols = {c["name"] for c in inspector.get_columns("products")}
    print("Colunas atuais em products:", sorted(cols))

    with engine.begin() as conn:
        add_column_if_missing(conn, cols, "code", "ALTER TABLE products ADD COLUMN code VARCHAR")
        add_column_if_missing(conn, cols, "description", "ALTER TABLE products ADD COLUMN description VARCHAR")
        add_column_if_missing(conn, cols, "unit", "ALTER TABLE products ADD COLUMN unit VARCHAR")
        add_column_if_missing(conn, cols, "min_stock", "ALTER TABLE products ADD COLUMN min_stock INTEGER NOT NULL DEFAULT 0")

    inspector = inspect(engine)
    cols_after = {c["name"] for c in inspector.get_columns("products")}
    print("Colunas finais em products:", sorted(cols_after))
    print("OK - schema de products atualizado.")
    

if __name__ == "__main__":
    main()