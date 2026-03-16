from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem

# RBAC
from app.models.rbac import Role, Permission, UserRole, RolePermission

# Empresa
from app.models.company import Company

# Outros relacionamentos futuros podem ser adicionados aqui
# Exemplo:
# from app.models.company_client import CompanyClient
# from app.models.company_order import CompanyOrder

__all__ = [
    "User",
    "Product",
    "Order",
    "OrderItem",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Company",
]