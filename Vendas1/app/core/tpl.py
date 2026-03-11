from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.core.flash import pop_flashes
from app.services.auth_service import get_current_user
from app.services.rbac_service import has_permission

templates = Jinja2Templates(directory="templates")

def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = {}
    if context:
        ctx.update(context)

    current_user = get_current_user(request)

    def can(permission_code: str) -> bool:
        if not current_user:
            return False
        return has_permission(int(current_user.id), permission_code)

    ctx.update({
        "request": request,
        "flashes": pop_flashes(request),
        "current_user": current_user,
        "can": can,  # ✅ para templates: {% if can("admin.dashboard.view") %}
    })
    return templates.TemplateResponse(name, ctx, status_code=status_code)

def attach_tpl(app: FastAPI) -> None:
    app.state.tpl = tpl