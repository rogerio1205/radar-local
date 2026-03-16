from urllib.parse import quote
from urllib.request import Request, urlopen
import json


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _safe_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_location_query(pais: str = "", estado: str = "", cidade: str = "", bairro: str = "") -> str:
    parts = []

    if bairro:
        parts.append(_safe_str(bairro))

    if cidade:
        parts.append(_safe_str(cidade))

    if estado:
        parts.append(_safe_str(estado))

    if pais:
        parts.append(_safe_str(pais))

    return ", ".join([p for p in parts if p])


def _normalize_term(value: str) -> str:
    text = _safe_str(value).lower()

    replacements = {
        "restaurantes": "restaurant",
        "restaurante": "restaurant",
        "lanchonetes": "fast_food",
        "lanchonete": "fast_food",
        "mercados": "supermarket",
        "mercado": "supermarket",
        "supermercados": "supermarket",
        "supermercado": "supermarket",
        "padarias": "bakery",
        "padaria": "bakery",
        "farmacias": "pharmacy",
        "farmácia": "pharmacy",
        "farmacia": "pharmacy",
        "cafeterias": "cafe",
        "cafeteria": "cafe",
        "bares": "bar",
        "bar": "bar",
        "hotéis": "hotel",
        "hoteis": "hotel",
        "hotel": "hotel",
        "postos": "fuel",
        "posto": "fuel",
        "academias": "gym",
        "academia": "gym",
        "petshop": "pet",
        "pet shop": "pet",
        "pets": "pet",
        "peixaria": "seafood",
        "peixarias": "seafood",
    }

    return replacements.get(text, text)


def _nominatim_search(query: str, limit: int = 1):
    if not query:
        return []

    url = f"{NOMINATIM_URL}?format=jsonv2&limit={int(limit)}&q={quote(query)}"
    request = Request(
        url,
        headers={
            "User-Agent": "RADAR-LOCAL/1.0 (places search service)"
        },
    )

    with urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def _get_area_bbox(pais: str = "", estado: str = "", cidade: str = "", bairro: str = "") -> dict:
    query = _build_location_query(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    result = _nominatim_search(query, limit=1)
    if not result:
        return {}

    item = result[0]

    boundingbox = item.get("boundingbox") or []
    lat = _safe_float(item.get("lat"), -14.2350)
    lng = _safe_float(item.get("lon"), -51.9253)

    if len(boundingbox) == 4:
        south = _safe_float(boundingbox[0], lat - 0.05)
        north = _safe_float(boundingbox[1], lat + 0.05)
        west = _safe_float(boundingbox[2], lng - 0.05)
        east = _safe_float(boundingbox[3], lng + 0.05)
    else:
        south = lat - 0.05
        north = lat + 0.05
        west = lng - 0.05
        east = lng + 0.05

    return {
        "label": query,
        "lat": lat,
        "lng": lng,
        "south": south,
        "north": north,
        "west": west,
        "east": east,
    }


def _build_overpass_query(south: float, west: float, north: float, east: float, raw_term: str) -> str:
    term = _safe_str(raw_term)
    normalized = _normalize_term(raw_term)

    if normalized == "restaurant":
        filters = f"""
        node["amenity"="restaurant"]({south},{west},{north},{east});
        way["amenity"="restaurant"]({south},{west},{north},{east});
        relation["amenity"="restaurant"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "supermarket":
        filters = f"""
        node["shop"="supermarket"]({south},{west},{north},{east});
        way["shop"="supermarket"]({south},{west},{north},{east});
        relation["shop"="supermarket"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "bakery":
        filters = f"""
        node["shop"="bakery"]({south},{west},{north},{east});
        way["shop"="bakery"]({south},{west},{north},{east});
        relation["shop"="bakery"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "pharmacy":
        filters = f"""
        node["amenity"="pharmacy"]({south},{west},{north},{east});
        way["amenity"="pharmacy"]({south},{west},{north},{east});
        relation["amenity"="pharmacy"]({south},{west},{north},{east});
        node["shop"="pharmacy"]({south},{west},{north},{east});
        way["shop"="pharmacy"]({south},{west},{north},{east});
        relation["shop"="pharmacy"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "cafe":
        filters = f"""
        node["amenity"="cafe"]({south},{west},{north},{east});
        way["amenity"="cafe"]({south},{west},{north},{east});
        relation["amenity"="cafe"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "bar":
        filters = f"""
        node["amenity"="bar"]({south},{west},{north},{east});
        way["amenity"="bar"]({south},{west},{north},{east});
        relation["amenity"="bar"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "hotel":
        filters = f"""
        node["tourism"="hotel"]({south},{west},{north},{east});
        way["tourism"="hotel"]({south},{west},{north},{east});
        relation["tourism"="hotel"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "fuel":
        filters = f"""
        node["amenity"="fuel"]({south},{west},{north},{east});
        way["amenity"="fuel"]({south},{west},{north},{east});
        relation["amenity"="fuel"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    elif normalized == "gym":
        filters = f"""
        node["leisure"="fitness_centre"]({south},{west},{north},{east});
        way["leisure"="fitness_centre"]({south},{west},{north},{east});
        relation["leisure"="fitness_centre"]({south},{west},{north},{east});
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        """
    else:
        filters = f"""
        node["name"~"{term}",i]({south},{west},{north},{east});
        way["name"~"{term}",i]({south},{west},{north},{east});
        relation["name"~"{term}",i]({south},{west},{north},{east});
        node["shop"~"{normalized}",i]({south},{west},{north},{east});
        way["shop"~"{normalized}",i]({south},{west},{north},{east});
        relation["shop"~"{normalized}",i]({south},{west},{north},{east});
        node["amenity"~"{normalized}",i]({south},{west},{north},{east});
        way["amenity"~"{normalized}",i]({south},{west},{north},{east});
        relation["amenity"~"{normalized}",i]({south},{west},{north},{east});
        node["office"~"{normalized}",i]({south},{west},{north},{east});
        way["office"~"{normalized}",i]({south},{west},{north},{east});
        relation["office"~"{normalized}",i]({south},{west},{north},{east});
        """

    return f"""
    [out:json][timeout:25];
    (
      {filters}
    );
    out center tags;
    """


def _overpass_search(south: float, west: float, north: float, east: float, search_term: str):
    query = _build_overpass_query(south, west, north, east, search_term)

    url = f"{OVERPASS_URL}?data={quote(query)}"
    request = Request(
        url,
        headers={
            "User-Agent": "RADAR-LOCAL/1.0 (places search service)"
        },
    )

    with urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def _extract_element_lat_lng(element: dict):
    lat = element.get("lat")
    lng = element.get("lon")

    if lat is not None and lng is not None:
        return _safe_float(lat), _safe_float(lng)

    center = element.get("center") or {}
    return _safe_float(center.get("lat")), _safe_float(center.get("lon"))


def _normalize_place(element: dict, area: dict, search_term: str) -> dict | None:
    tags = element.get("tags") or {}
    name = _safe_str(tags.get("name"))

    if not name:
        return None

    lat, lng = _extract_element_lat_lng(element)
    if lat is None or lng is None:
        return None

    street = _safe_str(tags.get("addr:street"))
    house_number = _safe_str(tags.get("addr:housenumber"))
    neighborhood = _safe_str(tags.get("addr:suburb")) or _safe_str(tags.get("addr:neighbourhood"))
    city = _safe_str(tags.get("addr:city"))
    state = _safe_str(tags.get("addr:state"))
    country = _safe_str(tags.get("addr:country"))
    postcode = _safe_str(tags.get("addr:postcode"))
    phone = _safe_str(tags.get("phone")) or _safe_str(tags.get("contact:phone"))
    website = _safe_str(tags.get("website")) or _safe_str(tags.get("contact:website"))
    instagram = _safe_str(tags.get("contact:instagram"))
    category = _safe_str(tags.get("shop")) or _safe_str(tags.get("amenity")) or _safe_str(tags.get("office")) or _safe_str(tags.get("craft")) or _safe_str(tags.get("tourism")) or _safe_str(tags.get("leisure"))
    description = _safe_str(tags.get("description"))

    address_parts = []
    if street:
        address_parts.append(street)
    if house_number:
        address_parts.append(house_number)

    address = ", ".join(address_parts)

    if not city:
        city = area.get("label", "")

    source_id = f"osm:{element.get('type', 'node')}:{element.get('id')}"

    return {
        "external_id": source_id,
        "source": "osm",
        "name": name,
        "category": category or _safe_str(search_term),
        "description": description,
        "phone": phone,
        "website": website,
        "instagram": instagram,
        "address": address,
        "neighborhood": neighborhood,
        "city": city,
        "state": state,
        "country": country,
        "postcode": postcode,
        "latitude": lat,
        "longitude": lng,
        "map_link": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=18/{lat}/{lng}",
    }


def search_places(pais: str = "", estado: str = "", cidade: str = "", bairro: str = "", q: str = "", limit: int = 30) -> list[dict]:
    search_term = _safe_str(q)
    if not search_term:
        return []

    area = _get_area_bbox(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    if not area:
        return []

    try:
        payload = _overpass_search(
            south=area["south"],
            west=area["west"],
            north=area["north"],
            east=area["east"],
            search_term=search_term,
        )
    except Exception:
        return []

    elements = payload.get("elements") or []
    results = []
    seen = set()

    for element in elements:
        item = _normalize_place(element, area, search_term)
        if not item:
            continue

        key = item["external_id"]
        if key in seen:
            continue

        seen.add(key)
        results.append(item)

        if len(results) >= int(limit):
            break

    return results