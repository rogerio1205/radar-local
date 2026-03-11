from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/empresas", tags=["products"])
templates = Jinja2Templates(directory="templates")


@router.get("/{empresa_id}/produtos", response_class=HTMLResponse)
def list_products(request: Request, empresa_id: int):
    """
    Lista produtos da empresa
    """
    return templates.TemplateResponse(
        "products_list.html",
        {
            "request": request,
            "empresa_id": empresa_id,
            "products": []
        }
    )


@router.get("/{empresa_id}/produtos/novo", response_class=HTMLResponse)
def new_product(request: Request, empresa_id: int):
    """
    Formulário de cadastro de produto
    """
    return templates.TemplateResponse(
        "product_form.html",
        {
            "request": request,
            "empresa_id": empresa_id
        }
    )