from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["map-view"])

@router.get("/mapa")
def mapa_removido():
    return JSONResponse(
        {
            "status": "desativado",
            "mensagem": "Rota /mapa removida. Use /mapa-v2"
        },
        status_code=410
    )