from sqlalchemy import inspect, text
from app.db.session import engine


def main():
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    if "companies" not in tables:
        print("Tabela 'companies' não existe.")
        return

    cols = {c["name"] for c in inspector.get_columns("companies")}
    print("Colunas atuais em companies:", sorted(cols))

    if "logo" not in cols:
        with engine.begin() as conn:
            print("Adicionando coluna: logo")
            conn.execute(text("ALTER TABLE companies ADD COLUMN logo VARCHAR"))

    inspector = inspect(engine)
    cols_after = {c["name"] for c in inspector.get_columns("companies")}
    print("Colunas finais em companies:", sorted(cols_after))
    print("OK - schema de companies atualizado.")
    

if __name__ == "__main__":
    main()