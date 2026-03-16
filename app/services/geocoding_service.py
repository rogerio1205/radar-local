from urllib.parse import quote
from urllib.request import Request, urlopen
import json


DEFAULT_CENTER = {
    "lat": -14.2350,
    "lng": -51.9253,
    "zoom": 4,
    "label": "Brasil",
}


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _build_query(pais: str = "", estado: str = "", cidade: str = "", bairro: str = "") -> str:
    parts = []

    if bairro and bairro.strip():
        parts.append(bairro.strip())

    if cidade and cidade.strip():
        parts.append(cidade.strip())

    if estado and estado.strip():
        parts.append(estado.strip())

    if pais and pais.strip():
        parts.append(pais.strip())

    return ", ".join(parts)


def _zoom_from_input(pais: str = "", estado: str = "", cidade: str = "", bairro: str = "") -> int:
    if bairro and bairro.strip():
        return 14

    if cidade and cidade.strip():
        return 11

    if estado and estado.strip():
        return 7

    if pais and pais.strip():
        return 5

    return 4


def geocode_region(pais: str = "", estado: str = "", cidade: str = "", bairro: str = "") -> dict:
    query = _build_query(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    if not query:
        return DEFAULT_CENTER.copy()

    url = f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={quote(query)}"

    headers = {
        "User-Agent": "RADAR-LOCAL/1.0 (FastAPI geocoding service)"
    }

    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        if not data:
            return {
                "lat": DEFAULT_CENTER["lat"],
                "lng": DEFAULT_CENTER["lng"],
                "zoom": _zoom_from_input(pais, estado, cidade, bairro),
                "label": query,
            }

        item = data[0]
        lat = _safe_float(item.get("lat"), DEFAULT_CENTER["lat"])
        lng = _safe_float(item.get("lon"), DEFAULT_CENTER["lng"])

        return {
            "lat": lat,
            "lng": lng,
            "zoom": _zoom_from_input(pais, estado, cidade, bairro),
            "label": query,
        }

    except Exception:
        return {
            "lat": DEFAULT_CENTER["lat"],
            "lng": DEFAULT_CENTER["lng"],
            "zoom": _zoom_from_input(pais, estado, cidade, bairro),
            "label": query or DEFAULT_CENTER["label"],
        }