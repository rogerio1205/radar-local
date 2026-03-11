from sqlalchemy.orm import Session
from sqlalchemy import text

ADMIN_ROLE = "admin"

PERMISSIONS = [
    ("admin.dashboard.view", "Ver dashboard admin"),
    ("admin.products.manage", "Gerenciar produtos"),
    ("admin.orders.read", "Ver pedidos"),
    ("admin.orders.update", "Atualizar pedidos"),
]

def ensure_rbac_seed(db: Session) -> None:
    # role admin
    role = db.execute(text("SELECT id FROM roles WHERE name = :n"), {"n": ADMIN_ROLE}).fetchone()
    if not role:
        db.execute(text("INSERT INTO roles (name) VALUES (:n)"), {"n": ADMIN_ROLE})
        db.commit()
        role = db.execute(text("SELECT id FROM roles WHERE name = :n"), {"n": ADMIN_ROLE}).fetchone()
    role_id = int(role[0])

    # permissions
    for code, desc in PERMISSIONS:
        p = db.execute(text("SELECT id FROM permissions WHERE code = :c"), {"c": code}).fetchone()
        if not p:
            db.execute(
                text("INSERT INTO permissions (code, description) VALUES (:c, :d)"),
                {"c": code, "d": desc},
            )
    db.commit()

    # link role_permissions
    for code, _ in PERMISSIONS:
        pid = db.execute(text("SELECT id FROM permissions WHERE code = :c"), {"c": code}).fetchone()
        pid = int(pid[0])
        exists = db.execute(
            text("SELECT 1 FROM role_permissions WHERE role_id = :r AND permission_id = :p"),
            {"r": role_id, "p": pid},
        ).fetchone()
        if not exists:
            db.execute(
                text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:r, :p)"),
                {"r": role_id, "p": pid},
            )
    db.commit()


def ensure_first_user_is_admin(db: Session, user_id: int) -> None:
    # já existe algum user_role com role admin?
    has_admin = db.execute(
        text(
            """
            SELECT 1
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE r.name = :n
            LIMIT 1
            """
        ),
        {"n": ADMIN_ROLE},
    ).fetchone()

    if has_admin:
        return

    role_id = db.execute(text("SELECT id FROM roles WHERE name = :n"), {"n": ADMIN_ROLE}).fetchone()
    if not role_id:
        return
    role_id = int(role_id[0])

    db.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:u, :r)"),
        {"u": int(user_id), "r": role_id},
    )
    db.commit()