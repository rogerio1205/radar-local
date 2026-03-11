import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# DB / Models
from app.db.session import Base, engine
import app.models

from app.core.flash import pop_flashes

# Routers WEB
from app.routers.web_auth import router as web_auth_router
from app.routers.web_store import router as web_store_router
from app.routers.store_public import router as store_public_router
from app.routers.stores_list import router as stores_list_router
from app.routers.map_view import router as map_view_router

# Routers API
from app.routers.api_users import router as api_users_router
from app.routers.api_products import router as api_products_router
from app.routers.api_orders import router as api_orders_router

# Empresa
from app.routers.company_register import router as company_register_router
from app.routers.company_panel import router as company_panel_router
from app.routers.company_products import router as company_products_router
from app.routers.company_data import router as company_data_router
from app.routers.company_clients import router as company_clients_router
from app.routers.company_orders import router as company_orders_router

# Admin
from app.routers.admin import router as admin_router

# Pagamentos
from app.routers.payment import router as payment_router


# ==========================================
# APP
# ==========================================

app = FastAPI(title=os.getenv("APP_NAME", "RADAR LOCAL"))

# STATIC
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# DB INIT
# ==========================================

AUTO_CREATE_DB = os.getenv("AUTO_CREATE_DB", "1") == "1"


@app.on_event("startup")
def on_startup():
    if AUTO_CREATE_DB:
        Base.metadata.create_all(bind=engine)


# ==========================================
# MIDDLEWARE
# ==========================================

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "radar-local-dev-secret"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# TEMPLATES
# ==========================================

templates = Jinja2Templates(directory="templates")


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = {}

    if context:
        ctx.update(context)

    ctx.update(
        {
            "request": request,
            "flashes": pop_flashes(request),
        }
    )

    return templates.TemplateResponse(name, ctx, status_code=status_code)


app.state.tpl = tpl

# ==========================================
# ROUTERS
# ==========================================

# WEB
app.include_router(web_auth_router)
app.include_router(web_store_router)
app.include_router(store_public_router)
app.include_router(stores_list_router)
app.include_router(map_view_router)

# API
app.include_router(api_users_router)
app.include_router(api_products_router)
app.include_router(api_orders_router)

# EMPRESA
app.include_router(company_register_router)
app.include_router(company_panel_router)
app.include_router(company_products_router)
app.include_router(company_data_router)
app.include_router(company_clients_router)
app.include_router(company_orders_router)

# ADMIN
app.include_router(admin_router)

# PAGAMENTOS
app.include_router(payment_router)

# ==========================================
# HEALTH CHECK
# ==========================================


@app.get("/health")
def health():
    return {"ok": True, "app": os.getenv("APP_NAME", "RADAR LOCAL")}