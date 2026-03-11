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

    with engine.begin() as conn:
        if "company_id" not in cols:
            print("Adicionando coluna: company_id")
            conn.execute(text("ALTER TABLE products ADD COLUMN company_id INTEGER"))

        if "weight" not in cols:
            print("Adicionando coluna: weight")
            conn.execute(text("ALTER TABLE products ADD COLUMN weight VARCHAR"))

        if "category" not in cols:
            print("Adicionando coluna: category")
            conn.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR"))

        if "active" not in cols:
            print("Adicionando coluna: active")
            conn.execute(text("ALTER TABLE products ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1"))

        if "stock" not in cols:
            print("Adicionando coluna: stock")
            conn.execute(text("ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 0"))

        if "price" not in cols:
            print("Adicionando coluna: price")
            conn.execute(text("ALTER TABLE products ADD COLUMN price FLOAT NOT NULL DEFAULT 0"))

    inspector = inspect(engine)
    cols_after = {c["name"] for c in inspector.get_columns("products")}
    print("Colunas finais em products:", sorted(cols_after))
    print("OK - schema de products corrigido.")


if __name__ == "__main__":
    main()