from __future__ import annotations

import re
from typing import Iterable


REGION_SCOPE = {
    "pais_padrao": "Brasil",
    "estado_padrao_sigla": "SP",
    "estado_padrao_nome": "São Paulo",
}

GENERIC_SEARCH_TERMS = {
    "farmacia", "farmárcia", "farmácia", "farmacias", "farmácias",
    "mercado", "mercados", "supermercado", "supermercados",
    "padaria", "padarias", "restaurante", "restaurantes",
    "lanchonete", "lanchonetes", "pizzaria", "pizzarias",
    "academia", "academias", "petshop", "pet shop", "posto", "postos",
    "material", "materiais", "loja", "lojas", "clinica", "clínica",
    "hospital", "drogaria", "drogarias", "remedio", "remédio",
}

STOPWORDS = {"de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "para"}

CATEGORY_SUGGESTIONS = [
    "Farmácia",
    "Supermercado",
    "Padaria",
    "Restaurante",
    "Pizzaria",
    "Pet Shop",
    "Academia",
    "Posto de Gasolina",
    "Material de Construção",
    "Clínica",
]

CITIES_SP = [
    {"value": "São Paulo", "aliases": ["sp", "sao paulo", "são paulo", "capital"]},
    {"value": "São Bernardo do Campo", "aliases": ["sbc", "sao bernardo do campo", "são bernardo do campo"]},
    {"value": "Santo André", "aliases": ["santo andre", "santo andré"]},
    {"value": "São Caetano do Sul", "aliases": ["sao caetano do sul", "são caetano do sul", "scs"]},
    {"value": "Diadema", "aliases": ["diadema"]},
    {"value": "Mauá", "aliases": ["maua", "mauá"]},
    {"value": "Ribeirão Pires", "aliases": ["ribeirao pires", "ribeirão pires"]},
    {"value": "Rio Grande da Serra", "aliases": ["rio grande da serra"]},
    {"value": "Guarulhos", "aliases": ["guarulhos"]},
    {"value": "Osasco", "aliases": ["osasco"]},
    {"value": "Barueri", "aliases": ["barueri"]},
    {"value": "Campinas", "aliases": ["campinas"]},
    {"value": "Santos", "aliases": ["santos"]},
    {"value": "Sorocaba", "aliases": ["sorocaba"]},
    {"value": "São José dos Campos", "aliases": ["sao jose dos campos", "são josé dos campos", "sjc"]},
    {"value": "Praia Grande", "aliases": ["praia grande"]},
    {"value": "São Vicente", "aliases": ["sao vicente", "são vicente"]},
]

NEIGHBORHOODS_BY_CITY = {
    "são paulo": ["Centro", "Sé", "Bela Vista", "Liberdade", "Pinheiros", "Itaim Bibi", "Moema", "Vila Mariana", "Tatuapé", "Ipiranga"],
    "são bernardo do campo": ["Centro", "Pauliceia", "Rudge Ramos", "Baeta Neves", "Assunção", "Demarchi", "Planalto", "Jordanópolis", "Alves Dias", "Nova Petrópolis"],
    "santo andré": ["Centro", "Vila Assunção", "Campestre", "Jardim", "Utinga", "Vila Luzita"],
    "são caetano do sul": ["Centro", "Santa Paula", "Barcelona", "Cerâmica", "Olímpico"],
    "diadema": ["Centro", "Eldorado", "Piraporinha", "Canhema", "Serraria"],
    "mauá": ["Centro", "Jardim Zaíra", "Vila Assis Brasil", "Parque São Vicente"],
    "ribeirão pires": ["Centro", "Santa Luzia", "Ouro Fino"],
    "rio grande da serra": ["Centro", "Jardim Encantado", "Santa Tereza"],
    "guarulhos": ["Centro", "Vila Galvão", "Picanço", "Bonsucesso", "Cumbica"],
    "osasco": ["Centro", "Vila Yara", "Jaguaribe", "Bela Vista"],
    "barueri": ["Centro", "Alphaville", "Jardim Belval", "Tamboré"],
    "campinas": ["Centro", "Cambuí", "Taquaral", "Barão Geraldo"],
    "santos": ["Centro", "Gonzaga", "Boqueirão", "Ponta da Praia"],
    "sorocaba": ["Centro", "Campolim", "Éden", "Jardim Europa"],
    "são josé dos campos": ["Centro", "Jardim Aquarius", "Santana", "Urbanova"],
    "praia grande": ["Canto do Forte", "Boqueirão", "Guilhermina", "Ocian"],
    "são vicente": ["Centro", "Itararé", "Gonzaguinha", "Japuí"],
}


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_text(value: str) -> str:
    text = _safe_text(value).lower()
    text = (
        text.replace("á", "a").replace("à", "a").replace("ã", "a").replace("â", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u").replace("ç", "c")
    )
    return " ".join(text.split())


def tokenize_query(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", normalize_text(value))
    return [token for token in tokens if token and token not in STOPWORDS]


def _term_matches(term: str, values: Iterable[str]) -> bool:
    raw_term = normalize_text(term)
    if not raw_term:
        return True
    for value in values:
        normalized = normalize_text(value)
        if normalized.startswith(raw_term) or raw_term in normalized:
            return True
    return False


def _build_item(value: str, field: str, subtitle: str = "") -> dict:
    return {"value": _safe_text(value), "label": _safe_text(value), "field": _safe_text(field), "subtitle": _safe_text(subtitle)}


def get_region_suggestions(field: str, term: str = "", pais: str = "Brasil", estado: str = "", cidade: str = "", limit: int = 8) -> list[dict]:
    normalized_field = normalize_text(field)
    normalized_country = normalize_text(pais)
    if normalized_country and normalized_country not in {"brasil", "brazil"}:
        return []

    if normalized_field == "pais":
        items = [_build_item("Brasil", "pais", "Busca inicial liberada para Brasil")]
        return [item for item in items if _term_matches(term, [item["value"], item["subtitle"]])][:limit]

    if normalized_field == "estado":
        items = [_build_item("SP", "estado", "São Paulo"), _build_item("São Paulo", "estado", "SP")]
        return [item for item in items if _term_matches(term, [item["value"], item["subtitle"]])][:limit]

    if normalized_field == "cidade":
        if estado and normalize_text(estado) not in {"sp", "sao paulo"}:
            return []
        result = []
        for city in CITIES_SP:
            if _term_matches(term, [city["value"], *city.get("aliases", [])]):
                result.append(_build_item(city["value"], "cidade", "São Paulo - SP"))
        return result[:limit]

    if normalized_field == "bairro":
        if estado and normalize_text(estado) not in {"sp", "sao paulo"}:
            return []
        city_norm = normalize_text(cidade)
        result = []
        if city_norm and city_norm in NEIGHBORHOODS_BY_CITY:
            city_label = next((c["value"] for c in CITIES_SP if normalize_text(c["value"]) == city_norm), cidade)
            for neighborhood in NEIGHBORHOODS_BY_CITY[city_norm]:
                if _term_matches(term, [neighborhood, city_label]):
                    result.append(_build_item(neighborhood, "bairro", city_label))
            return result[:limit]
        seen = set()
        for city in CITIES_SP:
            city_norm_key = normalize_text(city["value"])
            for neighborhood in NEIGHBORHOODS_BY_CITY.get(city_norm_key, []):
                key = (normalize_text(neighborhood), city_norm_key)
                if key in seen:
                    continue
                if _term_matches(term, [neighborhood, city["value"]]):
                    result.append(_build_item(neighborhood, "bairro", city["value"]))
                    seen.add(key)
        return result[:limit]

    return []


def _score_suggestion(term: str, target: str, subtitle: str = "") -> int:
    query = normalize_text(term)
    value = normalize_text(target)
    subtitle_value = normalize_text(subtitle)
    tokens = tokenize_query(term)
    score = 0
    if not query:
        return 10
    if query == value:
        score += 300
    elif value.startswith(query):
        score += 220
    elif query in value:
        score += 150
    if subtitle_value and query in subtitle_value:
        score += 40
    if tokens:
        hits_value = sum(1 for token in tokens if token in value)
        hits_subtitle = sum(1 for token in tokens if token in subtitle_value)
        score += hits_value * 35 + hits_subtitle * 10
        if all(token in value for token in tokens):
            score += 100
    return score


def get_search_suggestions(term: str, companies: list, products: list, estado: str = "", cidade: str = "", bairro: str = "", limit: int = 8) -> list[dict]:
    query = _safe_text(term)
    suggestions = []
    seen = set()

    def add_item(value: str, kind: str, subtitle: str = ""):
        clean_value = _safe_text(value)
        if not clean_value:
            return
        key = (normalize_text(clean_value), normalize_text(kind), normalize_text(subtitle))
        if key in seen:
            return
        score = _score_suggestion(query, clean_value, subtitle)
        if query and score <= 0:
            return
        suggestions.append({"value": clean_value, "label": clean_value, "type": kind, "subtitle": subtitle, "score": score})
        seen.add(key)

    for category in CATEGORY_SUGGESTIONS:
        add_item(category, "categoria", "Busca por categoria")

    for company in companies:
        company_city = _safe_text(getattr(company, "city", ""))
        company_state = _safe_text(getattr(company, "state", ""))
        company_neighborhood = _safe_text(getattr(company, "neighborhood", ""))
        company_address = _safe_text(getattr(company, "address", ""))
        company_name = _safe_text(getattr(company, "name", ""))

        if cidade and normalize_text(cidade) not in normalize_text(company_city) and normalize_text(cidade) not in normalize_text(company_address):
            continue
        if bairro and normalize_text(bairro) not in normalize_text(company_neighborhood) and normalize_text(bairro) not in normalize_text(company_address):
            continue
        if estado and normalize_text(estado) not in {normalize_text(company_state), "sp", "sao paulo"} and normalize_text(estado) not in normalize_text(company_address):
            continue

        subtitle = " • ".join([part for part in [company_neighborhood, company_city, company_state] if part])
        add_item(company_name, "empresa", subtitle or "Empresa cadastrada")
        add_item(company_address, "endereco", company_name or "Endereço de empresa")

    for product in products:
        product_name = _safe_text(getattr(product, "name", ""))
        product_category = _safe_text(getattr(product, "category", ""))
        company_id = getattr(product, "company_id", None)
        company_name = ""
        if company_id:
            related = next((c for c in companies if int(getattr(c, "id", 0) or 0) == int(company_id)), None)
            if related:
                company_name = _safe_text(getattr(related, "name", ""))
        subtitle = "Produto" if not company_name else f"Produto em {company_name}"
        add_item(product_name, "produto", subtitle)
        if product_category:
            add_item(product_category, "categoria", f"Categoria de produto • {company_name}" if company_name else "Categoria de produto")

    suggestions.sort(key=lambda item: (-int(item.get("score") or 0), normalize_text(item.get("label")), normalize_text(item.get("subtitle"))))

    if query and normalize_text(query) not in GENERIC_SEARCH_TERMS:
        strong = [item for item in suggestions if int(item.get("score") or 0) >= 120]
        if strong:
            suggestions = strong

    return suggestions[:limit]