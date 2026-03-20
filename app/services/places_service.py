import json
import math
import os
import re
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GOOGLE_PLACES_TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

GENERIC_SEARCH_TERMS = {
    "restaurant",
    "fast_food",
    "supermarket",
    "bakery",
    "pharmacy",
    "cafe",
    "bar",
    "hotel",
    "fuel",
    "gym",
    "pet",
    "store",
    "farmacia",
    "farmacias",
    "farmácia",
    "farmácias",
    "mercado",
    "mercados",
    "supermercado",
    "supermercados",
    "padaria",
    "padarias",
    "restaurante",
    "restaurantes",
    "lanchonete",
    "lanchonetes",
    "posto",
    "postos",
    "academia",
    "academias",
    "petshop",
    "pet shop",
    "remedio",
    "remedios",
    "remédio",
    "remédios",
    "medicamento",
    "medicamentos",
    "material",
    "materiais",
    "loja",
    "lojas",
}

STOPWORDS = {
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "em",
    "na",
    "no",
    "nas",
    "nos",
    "para",
}

SEARCH_EQUIVALENTS = {
    "farmacia": ["farmácia", "drogaria", "remedio", "remédio", "medicamento", "saude", "saúde"],
    "drogaria": ["farmacia", "farmácia", "remedio", "remédio", "medicamento", "saude", "saúde"],
    "supermercado": ["mercado", "mercearia", "atacarejo"],
    "mercado": ["supermercado", "mercearia", "atacarejo"],
    "padaria": ["panificadora", "bakery"],
    "restaurante": ["lanchonete", "food"],
    "petshop": ["pet shop", "pet", "veterinaria", "veterinária"],
    "material": ["construcao", "construção", "material de construcao", "material de construção", "obra"],
    "construcao": ["material", "obra", "material de construcao", "material de construção"],
    "lona": ["lonas", "toldo", "cobertura", "caminhao", "caminhão", "carreta"],
    "caminhao": ["caminhão", "carreta", "transporte"],
    "saude": ["saúde", "farmacia", "farmácia", "drogaria", "clinica", "clínica"],
}


def _expand_query_variants(value: str) -> list[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return []

    variants = [normalized]
    tokens = _tokenize_query(normalized)

    for token in tokens:
        for synonym in SEARCH_EQUIVALENTS.get(token, []):
            synonym_norm = _normalize_text(synonym)
            if synonym_norm and synonym_norm not in variants:
                variants.append(synonym_norm)

    phrase_swaps = {
        "material de construcao": ["material", "construcao", "obra"],
        "material de construção": ["material", "construcao", "obra"],
        "lona de caminhao": ["lona", "caminhao", "carreta", "toldo"],
        "lona de caminhão": ["lona", "caminhao", "carreta", "toldo"],
    }

    for phrase, replacements in phrase_swaps.items():
        if phrase in normalized:
            for item in replacements:
                item_norm = _normalize_text(item)
                if item_norm and item_norm not in variants:
                    variants.append(item_norm)

    return variants


def _expanded_tokens(value: str) -> list[str]:
    tokens = []
    seen = set()
    for variant in _expand_query_variants(value):
        for token in _tokenize_query(variant):
            if token not in seen:
                seen.add(token)
                tokens.append(token)
    return tokens


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_spaces(value: str) -> str:
    return " ".join(_safe_str(value).split())


def _normalize_text(value: str) -> str:
    text = _normalize_spaces(value).lower()
    text = (
        text.replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )
    return text


def _tokenize_query(value: str) -> list[str]:
    normalized = _normalize_text(value)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    return [token for token in tokens if token and token not in STOPWORDS]


def _contains_digits(value: str) -> bool:
    return any(char.isdigit() for char in _safe_str(value))


def _looks_like_address_query(value: str) -> bool:
    query = _normalize_text(value)
    tokens = _tokenize_query(query)

    if _contains_digits(query):
        return True

    address_terms = {
        "rua",
        "avenida",
        "av",
        "travessa",
        "alameda",
        "estrada",
        "rodovia",
        "praca",
        "praça",
        "numero",
        "n",
        "bairro",
    }

    return any(token in address_terms for token in tokens)


def _is_generic_query(value: str) -> bool:
    normalized = _normalize_text(value)
    if not normalized:
        return False

    if normalized in GENERIC_SEARCH_TERMS:
        return True

    tokens = _tokenize_query(normalized)
    if len(tokens) != 1:
        return False

    return tokens[0] in GENERIC_SEARCH_TERMS


def _all_tokens_present(tokens: list[str], text: str) -> bool:
    normalized = _normalize_text(text)
    if not tokens:
        return False
    return all(token in normalized for token in tokens)


def _count_tokens_present(tokens: list[str], text: str) -> int:
    normalized = _normalize_text(text)
    return sum(1 for token in tokens if token in normalized)


def _get_google_places_key() -> str:
    return _safe_str(
        os.getenv("GOOGLE_PLACES_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def _haversine_km(lat1, lng1, lat2, lng2) -> float | None:
    lat1 = _safe_float(lat1)
    lng1 = _safe_float(lng1)
    lat2 = _safe_float(lat2)
    lng2 = _safe_float(lng2)

    if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
        return None

    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _build_location_query(
    pais: str = "",
    estado: str = "",
    cidade: str = "",
    bairro: str = "",
) -> str:
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
        "remedio": "pharmacy",
        "remédio": "pharmacy",
        "medicamento": "pharmacy",
        "medicamentos": "pharmacy",
        "materiais": "store",
        "material": "store",
    }

    return replacements.get(text, text)


def _nominatim_search(query: str, limit: int = 1):
    if not query:
        return []

    url = f"{NOMINATIM_URL}?format=jsonv2&limit={int(limit)}&q={quote(query)}"
    request = Request(
        url,
        headers={"User-Agent": "ROTA-LOCAL/2.1 (places search service)"},
    )

    with urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def _get_area_bbox(
    pais: str = "",
    estado: str = "",
    cidade: str = "",
    bairro: str = "",
) -> dict:
    query = _build_location_query(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    if not query:
        query = "Brasil"

    result = _nominatim_search(query, limit=1)
    if not result:
        return {
            "label": query,
            "lat": -14.2350,
            "lng": -51.9253,
            "south": -14.7350,
            "north": -13.7350,
            "west": -52.4253,
            "east": -51.4253,
        }

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


def _build_overpass_query(
    south: float,
    west: float,
    north: float,
    east: float,
    raw_term: str,
) -> str:
    term = _safe_str(raw_term)
    normalized = _normalize_term(raw_term)

    return f'''
    [out:json][timeout:25];
    (
      node["name"~"{term}",i]({south},{west},{north},{east});
      way["name"~"{term}",i]({south},{west},{north},{east});
      relation["name"~"{term}",i]({south},{west},{north},{east});
      node["brand"~"{term}",i]({south},{west},{north},{east});
      way["brand"~"{term}",i]({south},{west},{north},{east});
      relation["brand"~"{term}",i]({south},{west},{north},{east});
      node["addr:street"~"{term}",i]({south},{west},{north},{east});
      way["addr:street"~"{term}",i]({south},{west},{north},{east});
      relation["addr:street"~"{term}",i]({south},{west},{north},{east});
      node["shop"~"{normalized}",i]({south},{west},{north},{east});
      way["shop"~"{normalized}",i]({south},{west},{north},{east});
      relation["shop"~"{normalized}",i]({south},{west},{north},{east});
      node["amenity"~"{normalized}",i]({south},{west},{north},{east});
      way["amenity"~"{normalized}",i]({south},{west},{north},{east});
      relation["amenity"~"{normalized}",i]({south},{west},{north},{east});
      node["office"~"{normalized}",i]({south},{west},{north},{east});
      way["office"~"{normalized}",i]({south},{west},{north},{east});
      relation["office"~"{normalized}",i]({south},{west},{north},{east});
    );
    out center tags;
    '''


def _overpass_search(
    south: float,
    west: float,
    north: float,
    east: float,
    search_term: str,
):
    query = _build_overpass_query(south, west, north, east, search_term)

    url = f"{OVERPASS_URL}?data={quote(query)}"
    request = Request(
        url,
        headers={"User-Agent": "ROTA-LOCAL/2.1 (places search service)"},
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


def _extract_city_state_from_address(address: str) -> tuple[str, str]:
    text = _normalize_spaces(address)
    if not text:
        return "", ""

    parts = [p.strip() for p in text.split(",") if p.strip()]
    city = ""
    state = ""

    for i, part in enumerate(parts):
        lower = part.lower()

        if lower in {"brasil", "brazil"}:
            continue

        if len(part) == 2 and part.isalpha():
            state = part.upper()
            if i > 0 and not city:
                city = parts[i - 1]
            break

        tokens = part.split()
        if len(tokens) >= 2 and len(tokens[-1]) == 2 and tokens[-1].isalpha():
            state = tokens[-1].upper()
            city = " ".join(tokens[:-1]).strip()
            break

    return city, state


def _normalize_place(element: dict, fallback_category: str = "") -> dict:
    tags = element.get("tags") or {}
    lat, lng = _extract_element_lat_lng(element)

    name = (
        tags.get("name")
        or tags.get("brand")
        or tags.get("operator")
        or "Empresa sem nome"
    )

    address_parts = [
        tags.get("addr:street"),
        tags.get("addr:housenumber"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:state"),
    ]
    address = ", ".join([_safe_str(x) for x in address_parts if _safe_str(x)])

    city = _safe_str(tags.get("addr:city"))
    state = _safe_str(tags.get("addr:state"))
    neighborhood = _safe_str(tags.get("addr:suburb"))
    phone = _safe_str(tags.get("phone") or tags.get("contact:phone"))

    category = (
        _safe_str(tags.get("shop"))
        or _safe_str(tags.get("amenity"))
        or _safe_str(tags.get("tourism"))
        or _safe_str(tags.get("office"))
        or _safe_str(fallback_category)
    )

    map_link = ""
    if lat is not None and lng is not None:
        map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

    return {
        "external_id": f"osm-{element.get('type', 'node')}-{element.get('id', '')}",
        "source": "openstreetmap",
        "name": _safe_str(name),
        "address": _safe_str(address),
        "city": city,
        "state": state,
        "neighborhood": neighborhood,
        "country": "Brasil",
        "phone": phone,
        "website": "",
        "latitude": "" if lat is None else str(lat),
        "longitude": "" if lng is None else str(lng),
        "category": category,
        "description": f"Empresa encontrada no mapa para a busca: {_safe_str(fallback_category)}",
        "map_link": map_link,
    }


def _dedupe_places(items: list[dict]) -> list[dict]:
    seen = set()
    result = []

    for item in items:
        external_id = _safe_str(item.get("external_id")).lower()
        name = _safe_str(item.get("name")).lower()
        address = _safe_str(item.get("address")).lower()
        city = _safe_str(item.get("city")).lower()
        state = _safe_str(item.get("state")).lower()

        key = external_id or f"{name}|{address}|{city}|{state}"
        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def _build_search_queries(
    q: str = "",
    pais: str = "",
    estado: str = "",
    cidade: str = "",
    bairro: str = "",
) -> list[str]:
    q = _normalize_spaces(q)
    pais = _normalize_spaces(pais)
    estado = _normalize_spaces(estado)
    cidade = _normalize_spaces(cidade)
    bairro = _normalize_spaces(bairro)

    if not q:
        return []

    location_parts = [bairro, cidade, estado, pais]
    location_text = ", ".join([x for x in location_parts if x])

    q_lower = q.lower()
    location_tokens = [pais.lower(), estado.lower(), cidade.lower(), bairro.lower(), "brasil", "brazil"]
    has_location_in_q = any(token and token in q_lower for token in location_tokens)

    base_variants = [q]
    for variant in _expand_query_variants(q):
        if variant and _normalize_text(variant) != _normalize_text(q):
            base_variants.append(variant)

    queries = []
    for variant in base_variants:
        variant = _normalize_spaces(variant)
        if not variant:
            continue
        if not has_location_in_q:
            queries.append(variant)
        if location_text and not has_location_in_q:
            queries.append(f"{variant}, {location_text}")
        elif has_location_in_q:
            queries.append(variant)
        elif pais:
            queries.append(f"{variant}, {pais}")
        else:
            queries.append(f"{variant}, Brasil")

    dedup = []
    seen = set()
    for item in queries:
        key = _normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            dedup.append(item)

    return dedup


def _google_request(url: str, params: dict) -> dict:
    final_url = f"{url}?{urlencode(params)}"
    request = Request(
        final_url,
        headers={"User-Agent": "ROTA-LOCAL/2.1 (google places search service)"},
    )

    with urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def _google_place_types_to_category(types: list) -> str:
    if not types:
        return ""

    priority = [
        "restaurant",
        "bakery",
        "pharmacy",
        "supermarket",
        "cafe",
        "bar",
        "gym",
        "lodging",
        "gas_station",
        "store",
        "food",
        "shopping_mall",
        "hospital",
        "school",
    ]

    normalized = [str(t).strip() for t in types if str(t).strip()]

    for item in priority:
        if item in normalized:
            return item

    return normalized[0] if normalized else ""


def _google_build_map_link(place_id: str = "", lat: str = "", lng: str = "") -> str:
    place_id = _safe_str(place_id)
    lat = _safe_str(lat)
    lng = _safe_str(lng)

    if place_id:
        return f"https://www.google.com/maps/search/?api=1&query_place_id={quote(place_id)}"

    if lat and lng:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

    return ""


def _google_fetch_place_details(place_id: str, api_key: str) -> dict:
    place_id = _safe_str(place_id)
    if not place_id:
        return {}

    try:
        data = _google_request(
            GOOGLE_PLACE_DETAILS_URL,
            {
                "place_id": place_id,
                "fields": "formatted_phone_number,international_phone_number,website,url",
                "language": "pt-BR",
                "region": "br",
                "key": api_key,
            },
        )
    except Exception:
        return {}

    if _safe_str(data.get("status")) not in {"OK", ""}:
        return {}

    return data.get("result") or {}


def _normalize_google_place(item: dict, api_key: str = "", origin_lat: str = "", origin_lng: str = "") -> dict:
    geometry = item.get("geometry") or {}
    location = geometry.get("location") or {}

    lat = _safe_float(location.get("lat"))
    lng = _safe_float(location.get("lng"))

    address = _safe_str(item.get("formatted_address"))
    city, state = _extract_city_state_from_address(address)

    place_id = _safe_str(item.get("place_id"))
    category = _google_place_types_to_category(item.get("types") or [])

    phone = ""
    website = ""
    google_url = ""

    if api_key and place_id:
        details = _google_fetch_place_details(place_id, api_key)
        phone = _safe_str(
            details.get("formatted_phone_number")
            or details.get("international_phone_number")
        )
        website = _safe_str(details.get("website"))
        google_url = _safe_str(details.get("url"))

    map_link = google_url or _google_build_map_link(
        place_id=place_id,
        lat="" if lat is None else str(lat),
        lng="" if lng is None else str(lng),
    )

    distance_km = _haversine_km(origin_lat, origin_lng, lat, lng)

    return {
        "external_id": place_id or f"google-{_safe_str(item.get('name'))}-{_safe_str(address)}",
        "source": "google_places",
        "name": _safe_str(item.get("name")),
        "address": address,
        "city": city,
        "state": state,
        "neighborhood": "",
        "country": "Brasil",
        "phone": phone,
        "website": website,
        "latitude": "" if lat is None else str(lat),
        "longitude": "" if lng is None else str(lng),
        "category": category,
        "description": _safe_str(item.get("business_status")) or "Empresa encontrada via Google Places.",
        "map_link": map_link,
        "distance_km": distance_km,
    }


def _google_text_search_page(
    query_text: str,
    latitude: str = "",
    longitude: str = "",
    radius_meters: int = 0,
    pagetoken: str = "",
) -> dict:
    api_key = _get_google_places_key()
    if not api_key:
        return {"status": "NO_API_KEY", "results": []}

    params = {
        "language": "pt-BR",
        "region": "br",
        "key": api_key,
    }

    if pagetoken:
        params["pagetoken"] = pagetoken
    else:
        params["query"] = query_text

        lat = _safe_float(latitude)
        lng = _safe_float(longitude)
        radius_meters = _safe_int(radius_meters, 0)

        if lat is not None and lng is not None:
            params["location"] = f"{lat},{lng}"
            if radius_meters > 0:
                params["radius"] = str(radius_meters)

    try:
        return _google_request(GOOGLE_PLACES_TEXTSEARCH_URL, params)
    except Exception:
        return {"status": "REQUEST_ERROR", "results": []}


def _google_search_single_query(
    query_text: str,
    latitude: str = "",
    longitude: str = "",
    radius_meters: int = 0,
    limit: int = 20,
) -> list[dict]:
    api_key = _get_google_places_key()
    if not api_key:
        return []

    collected = []
    next_page_token = ""
    attempts = 0

    while len(collected) < int(limit) and attempts < 3:
        data = _google_text_search_page(
            query_text=query_text,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            pagetoken=next_page_token,
        )

        status = _safe_str(data.get("status"))
        results = data.get("results") or []

        if status == "INVALID_REQUEST" and next_page_token:
            time.sleep(2)
            attempts += 1
            continue

        if status not in {"OK", "ZERO_RESULTS", "INVALID_REQUEST"} and not results:
            break

        for item in results:
            collected.append(
                _normalize_google_place(
                    item,
                    api_key=api_key,
                    origin_lat=latitude,
                    origin_lng=longitude,
                )
            )
            if len(collected) >= int(limit):
                break

        next_page_token = _safe_str(data.get("next_page_token"))
        attempts += 1

        if not next_page_token or len(collected) >= int(limit):
            break

        time.sleep(2)

    return _dedupe_places(collected[: int(limit)])


def _expand_radius_steps(radius_meters: int) -> list[int]:
    radius_meters = _safe_int(radius_meters, 0)

    if radius_meters <= 0:
        return [0]

    steps = [radius_meters]

    multipliers = [2, 5, 10]
    for mult in multipliers:
        candidate = radius_meters * mult
        if candidate not in steps:
            steps.append(candidate)

    cap = max(radius_meters, 50000)
    if cap not in steps:
        steps.append(cap)

    return steps


def _filter_and_sort_by_exact_radius(items: list[dict], latitude: str = "", longitude: str = "", exact_radius_meters: int = 0) -> list[dict]:
    results = _dedupe_places(items)

    origin_lat = _safe_float(latitude)
    origin_lng = _safe_float(longitude)
    exact_radius_km = _safe_int(exact_radius_meters, 0) / 1000 if exact_radius_meters else 0

    if origin_lat is None or origin_lng is None:
        return results

    filtered = []

    for item in results:
        distance_km = item.get("distance_km")
        if distance_km is None:
            distance_km = _haversine_km(origin_lat, origin_lng, item.get("latitude"), item.get("longitude"))
            item["distance_km"] = distance_km

        if exact_radius_km <= 0:
            filtered.append(item)
            continue

        if distance_km is not None and float(distance_km) <= exact_radius_km:
            filtered.append(item)

    filtered.sort(
        key=lambda x: (
            999999 if x.get("distance_km") is None else float(x.get("distance_km")),
            _safe_str(x.get("name")).lower(),
        )
    )

    return filtered


def _score_place_match(item: dict, q: str) -> int:
    query = _normalize_text(q)
    variants = _expand_query_variants(q)
    tokens = _expanded_tokens(q)

    if not query:
        return 0

    name = _normalize_text(item.get("name"))
    address = _normalize_text(item.get("address"))
    city = _normalize_text(item.get("city"))
    state = _normalize_text(item.get("state"))
    neighborhood = _normalize_text(item.get("neighborhood"))
    category = _normalize_text(item.get("category"))
    description = _normalize_text(item.get("description"))

    score = 0

    for variant in variants:
        if variant == name:
            score = max(score, 260)
        elif name.startswith(variant):
            score = max(score, 230)
        elif variant in name:
            score = max(score, 190)

        if variant == address:
            score = max(score, score + 220)
        elif address.startswith(variant):
            score += 70
        elif variant in address:
            score += 45

        if variant and variant in neighborhood:
            score += 22
        if variant and variant in city:
            score += 16
        if variant and variant in state:
            score += 8
        if variant and variant in category:
            score += 28
        if variant and variant in description:
            score += 14

    if tokens:
        name_hits = _count_tokens_present(tokens, name)
        address_hits = _count_tokens_present(tokens, address)
        category_hits = _count_tokens_present(tokens, category)
        description_hits = _count_tokens_present(tokens, description)

        score += name_hits * 35
        score += address_hits * 20
        score += category_hits * 20
        score += description_hits * 10

        if _all_tokens_present(tokens, name):
            score += 120
        if _all_tokens_present(tokens, address):
            score += 80
        if _all_tokens_present(tokens, f"{neighborhood} {city} {state}"):
            score += 50
        if _all_tokens_present(tokens, f"{category} {description}"):
            score += 40

    if _looks_like_address_query(q):
        if query in address:
            score += 120
        if _all_tokens_present(tokens, address):
            score += 80

    generic_query = _is_generic_query(q)
    if generic_query:
        for variant in variants:
            normalized_generic = _normalize_term(variant)
            if normalized_generic and normalized_generic in category:
                score += 80
            if normalized_generic and normalized_generic in description:
                score += 26

    if not generic_query and score < 90 and not any(variant in name or variant in address for variant in variants):
        score = 0

    return score


def _apply_query_ranking(items: list[dict], q: str, limit: int = 20) -> list[dict]:
    ranked = []

    for item in _dedupe_places(items):
        score = _score_place_match(item, q)
        if score <= 0:
            continue
        item["search_score"] = score
        ranked.append(item)

    ranked.sort(
        key=lambda x: (
            -int(x.get("search_score") or 0),
            999999 if x.get("distance_km") is None else float(x.get("distance_km")),
            _safe_str(x.get("name")).lower(),
        )
    )

    if not ranked:
        return []

    if not _is_generic_query(q):
        strong_matches = [item for item in ranked if int(item.get("search_score") or 0) >= 160]
        if strong_matches:
            return strong_matches[: int(limit)]

    return ranked[: int(limit)]


def _google_search_places(
    q: str,
    pais: str = "",
    estado: str = "",
    cidade: str = "",
    bairro: str = "",
    latitude: str = "",
    longitude: str = "",
    radius_meters: int = 0,
    limit: int = 20,
) -> list[dict]:
    origin_lat = _safe_float(latitude)
    origin_lng = _safe_float(longitude)
    query_variants = _build_search_queries(
        q=q,
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    if not query_variants:
        return []

    search_limits = max(int(limit), 20)

    if origin_lat is None or origin_lng is None or radius_meters <= 0:
        collected = []
        for query_text in query_variants:
            collected.extend(
                _google_search_single_query(
                    query_text=query_text,
                    latitude=latitude,
                    longitude=longitude,
                    radius_meters=radius_meters,
                    limit=search_limits,
                )
            )

        filtered = _filter_and_sort_by_exact_radius(
            collected,
            latitude=latitude,
            longitude=longitude,
            exact_radius_meters=radius_meters,
        )
        return _apply_query_ranking(filtered, q=q, limit=limit)

    collected = []

    for search_radius in _expand_radius_steps(radius_meters):
        for query_text in query_variants:
            batch = _google_search_single_query(
                query_text=query_text,
                latitude=latitude,
                longitude=longitude,
                radius_meters=search_radius,
                limit=max(search_limits, 60),
            )
            collected.extend(batch)

        exact_filtered = _filter_and_sort_by_exact_radius(
            collected,
            latitude=latitude,
            longitude=longitude,
            exact_radius_meters=radius_meters,
        )
        ranked = _apply_query_ranking(exact_filtered, q=q, limit=limit)

        if len(ranked) >= int(limit):
            return ranked[: int(limit)]

    final_filtered = _filter_and_sort_by_exact_radius(
        collected,
        latitude=latitude,
        longitude=longitude,
        exact_radius_meters=radius_meters,
    )

    return _apply_query_ranking(final_filtered, q=q, limit=limit)


def _fallback_osm_search(
    pais: str = "",
    estado: str = "",
    cidade: str = "",
    bairro: str = "",
    q: str = "",
    latitude: str = "",
    longitude: str = "",
    radius_meters: int = 0,
    limit: int = 20,
) -> list[dict]:
    bbox = _get_area_bbox(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
    )

    result = _overpass_search(
        south=bbox["south"],
        west=bbox["west"],
        north=bbox["north"],
        east=bbox["east"],
        search_term=q,
    )

    elements = result.get("elements") or []
    normalized = [_normalize_place(element, fallback_category=q) for element in elements]
    normalized = [item for item in normalized if item and _safe_str(item.get("name"))]

    origin_lat = _safe_float(latitude)
    origin_lng = _safe_float(longitude)
    radius_km = _safe_int(radius_meters, 0) / 1000 if radius_meters else 0

    if origin_lat is not None and origin_lng is not None:
        filtered = []
        for item in normalized:
            distance_km = _haversine_km(origin_lat, origin_lng, item.get("latitude"), item.get("longitude"))
            item["distance_km"] = distance_km
            if radius_km <= 0:
                filtered.append(item)
            elif distance_km is not None and distance_km <= radius_km:
                filtered.append(item)

        return _apply_query_ranking(filtered, q=q, limit=limit)

    return _apply_query_ranking(normalized, q=q, limit=limit)


def search_places(
    pais: str = "",
    estado: str = "",
    cidade: str = "",
    bairro: str = "",
    q: str = "",
    latitude: str = "",
    longitude: str = "",
    radius_meters: int = 0,
    limit: int = 20,
) -> list[dict]:
    q = _normalize_spaces(q)

    if not q:
        return []

    google_results = _google_search_places(
        q=q,
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit,
    )

    if google_results:
        return google_results

    return _fallback_osm_search(
        pais=pais,
        estado=estado,
        cidade=cidade,
        bairro=bairro,
        q=q,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit,
    )