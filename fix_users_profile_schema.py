import sqlite3


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    return any(col[1] == column_name for col in cols)


def main():
    conn = sqlite3.connect("vendas.db")
    cur = conn.cursor()

    if not column_exists(cur, "users", "phone"):
        cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        print("Coluna phone adicionada com sucesso.")
    else:
        print("Coluna phone já existe.")

    if not column_exists(cur, "users", "address"):
        cur.execute("ALTER TABLE users ADD COLUMN address TEXT")
        print("Coluna address adicionada com sucesso.")
    else:
        print("Coluna address já existe.")

    conn.commit()
    conn.close()
    print("Schema de users atualizado com sucesso.")


if __name__ == "__main__":
    main()