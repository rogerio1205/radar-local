import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["map-v2"])


def tpl(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    return request.app.state.tpl(request, name, context, status_code)


def _get_google_maps_browser_key() -> str:
    return (
        os.getenv("GOOGLE_MAPS_JS_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
        or os.getenv("GOOGLE_PLACES_API_KEY")
        or ""
    ).strip()


@router.get("/mapa-v2", response_class=HTMLResponse)
def mapa_v2(request: Request):
    key = _get_google_maps_browser_key()

    print("DEBUG GOOGLE KEY:", key)

    return tpl(
        request,
        "mapa_v2.html",
        {
            "google_maps_js_key": key,
        },
    )