from sqlalchemy import inspect, text
from app.db.session import engine


def main():
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    if "products" not in tables:
        print("Tabela 'products' não existe.")
        return

    cols = {c["name"] for c in inspector.get_columns("products")}
    print("Colunas atuais em products:", sorted(cols))

    if "image" not in cols:
        with engine.begin() as conn:
            print("Adicionando coluna: image")
            conn.execute(text("ALTER TABLE products ADD COLUMN image VARCHAR"))

    inspector = inspect(engine)
    cols_after = {c["name"] for c in inspector.get_columns("products")}
    print("Colunas finais em products:", sorted(cols_after))
    print("OK - schema de products atualizado.")


if __name__ == "__main__":
    main()