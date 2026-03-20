from typing import Iterable


REGION_SCOPE = {
    "pais_padrao": "Brasil",
    "estado_padrao_sigla": "SP",
    "estado_padrao_nome": "São Paulo",
}


BRAZIL_STATES = [
    {"sigla": "AC", "nome": "Acre", "aliases": ["acre", "ac"]},
    {"sigla": "AL", "nome": "Alagoas", "aliases": ["alagoas", "al"]},
    {"sigla": "AP", "nome": "Amapá", "aliases": ["amapa", "amapá", "ap"]},
    {"sigla": "AM", "nome": "Amazonas", "aliases": ["amazonas", "am"]},
    {"sigla": "BA", "nome": "Bahia", "aliases": ["bahia", "ba"]},
    {"sigla": "CE", "nome": "Ceará", "aliases": ["ceara", "ceará", "ce"]},
    {"sigla": "DF", "nome": "Distrito Federal", "aliases": ["distrito federal", "brasilia", "brasília", "df"]},
    {"sigla": "ES", "nome": "Espírito Santo", "aliases": ["espirito santo", "espírito santo", "es"]},
    {"sigla": "GO", "nome": "Goiás", "aliases": ["goias", "goiás", "go"]},
    {"sigla": "MA", "nome": "Maranhão", "aliases": ["maranhao", "maranhão", "ma"]},
    {"sigla": "MT", "nome": "Mato Grosso", "aliases": ["mato grosso", "mt"]},
    {"sigla": "MS", "nome": "Mato Grosso do Sul", "aliases": ["mato grosso do sul", "ms"]},
    {"sigla": "MG", "nome": "Minas Gerais", "aliases": ["minas gerais", "mg"]},
    {"sigla": "PA", "nome": "Pará", "aliases": ["para", "pará", "pa"]},
    {"sigla": "PB", "nome": "Paraíba", "aliases": ["paraiba", "paraíba", "pb"]},
    {"sigla": "PR", "nome": "Paraná", "aliases": ["parana", "paraná", "pr"]},
    {"sigla": "PE", "nome": "Pernambuco", "aliases": ["pernambuco", "pe"]},
    {"sigla": "PI", "nome": "Piauí", "aliases": ["piaui", "piauí", "pi"]},
    {"sigla": "RJ", "nome": "Rio de Janeiro", "aliases": ["rio de janeiro", "rj"]},
    {"sigla": "RN", "nome": "Rio Grande do Norte", "aliases": ["rio grande do norte", "rn"]},
    {"sigla": "RS", "nome": "Rio Grande do Sul", "aliases": ["rio grande do sul", "rs"]},
    {"sigla": "RO", "nome": "Rondônia", "aliases": ["rondonia", "rondônia", "ro"]},
    {"sigla": "RR", "nome": "Roraima", "aliases": ["roraima", "rr"]},
    {"sigla": "SC", "nome": "Santa Catarina", "aliases": ["santa catarina", "sc"]},
    {"sigla": "SP", "nome": "São Paulo", "aliases": ["sao paulo", "são paulo", "sp"]},
    {"sigla": "SE", "nome": "Sergipe", "aliases": ["sergipe", "se"]},
    {"sigla": "TO", "nome": "Tocantins", "aliases": ["tocantins", "to"]},
]


BRAZIL_CITIES = [
    {"value": "São Paulo", "state": "SP", "aliases": ["sp", "sao paulo", "são paulo", "capital"]},
    {"value": "São Bernardo do Campo", "state": "SP", "aliases": ["sbc", "sao bernardo do campo", "são bernardo do campo"]},
    {"value": "Santo André", "state": "SP", "aliases": ["santo andre", "santo andré"]},
    {"value": "São Caetano do Sul", "state": "SP", "aliases": ["sao caetano do sul", "são caetano do sul", "scs"]},
    {"value": "Diadema", "state": "SP", "aliases": ["diadema"]},
    {"value": "Mauá", "state": "SP", "aliases": ["maua", "mauá"]},
    {"value": "Ribeirão Pires", "state": "SP", "aliases": ["ribeirao pires", "ribeirão pires"]},
    {"value": "Rio Grande da Serra", "state": "SP", "aliases": ["rio grande da serra"]},
    {"value": "Guarulhos", "state": "SP", "aliases": ["guarulhos"]},
    {"value": "Osasco", "state": "SP", "aliases": ["osasco"]},
    {"value": "Barueri", "state": "SP", "aliases": ["barueri"]},
    {"value": "Campinas", "state": "SP", "aliases": ["campinas"]},
    {"value": "Santos", "state": "SP", "aliases": ["santos"]},
    {"value": "Sorocaba", "state": "SP", "aliases": ["sorocaba"]},
    {"value": "São José dos Campos", "state": "SP", "aliases": ["sao jose dos campos", "são josé dos campos", "sjc"]},
    {"value": "Praia Grande", "state": "SP", "aliases": ["praia grande"]},
    {"value": "São Vicente", "state": "SP", "aliases": ["sao vicente", "são vicente"]},
    {"value": "Rio de Janeiro", "state": "RJ", "aliases": ["rio de janeiro", "rj", "rio"]},
    {"value": "Niterói", "state": "RJ", "aliases": ["niteroi", "niterói"]},
    {"value": "Duque de Caxias", "state": "RJ", "aliases": ["duque de caxias"]},
    {"value": "Belo Horizonte", "state": "MG", "aliases": ["belo horizonte", "bh"]},
    {"value": "Uberlândia", "state": "MG", "aliases": ["uberlandia", "uberlândia"]},
    {"value": "Contagem", "state": "MG", "aliases": ["contagem"]},
    {"value": "Curitiba", "state": "PR", "aliases": ["curitiba"]},
    {"value": "Londrina", "state": "PR", "aliases": ["londrina"]},
    {"value": "Maringá", "state": "PR", "aliases": ["maringa", "maringá"]},
    {"value": "Porto Alegre", "state": "RS", "aliases": ["porto alegre"]},
    {"value": "Caxias do Sul", "state": "RS", "aliases": ["caxias do sul"]},
    {"value": "Florianópolis", "state": "SC", "aliases": ["florianopolis", "florianópolis"]},
    {"value": "Joinville", "state": "SC", "aliases": ["joinville"]},
    {"value": "Salvador", "state": "BA", "aliases": ["salvador"]},
    {"value": "Feira de Santana", "state": "BA", "aliases": ["feira de santana"]},
    {"value": "Recife", "state": "PE", "aliases": ["recife"]},
    {"value": "Jaboatão dos Guararapes", "state": "PE", "aliases": ["jaboatao dos guararapes", "jaboatão dos guararapes"]},
    {"value": "Fortaleza", "state": "CE", "aliases": ["fortaleza"]},
    {"value": "Caucaia", "state": "CE", "aliases": ["caucaia"]},
    {"value": "Brasília", "state": "DF", "aliases": ["brasilia", "brasília", "df"]},
    {"value": "Goiânia", "state": "GO", "aliases": ["goiania", "goiânia"]},
    {"value": "Aparecida de Goiânia", "state": "GO", "aliases": ["aparecida de goiania", "aparecida de goiânia"]},
    {"value": "Manaus", "state": "AM", "aliases": ["manaus"]},
    {"value": "Belém", "state": "PA", "aliases": ["belem", "belém"]},
    {"value": "Ananindeua", "state": "PA", "aliases": ["ananindeua"]},
    {"value": "São Luís", "state": "MA", "aliases": ["sao luis", "são luís", "são luiz"]},
    {"value": "João Pessoa", "state": "PB", "aliases": ["joao pessoa", "joão pessoa"]},
    {"value": "Natal", "state": "RN", "aliases": ["natal"]},
    {"value": "Teresina", "state": "PI", "aliases": ["teresina"]},
    {"value": "Aracaju", "state": "SE", "aliases": ["aracaju"]},
    {"value": "Maceió", "state": "AL", "aliases": ["maceio", "maceió"]},
    {"value": "Palmas", "state": "TO", "aliases": ["palmas"]},
    {"value": "Porto Velho", "state": "RO", "aliases": ["porto velho"]},
    {"value": "Boa Vista", "state": "RR", "aliases": ["boa vista"]},
    {"value": "Macapá", "state": "AP", "aliases": ["macapa", "macapá"]},
    {"value": "Rio Branco", "state": "AC", "aliases": ["rio branco"]},
    {"value": "Cuiabá", "state": "MT", "aliases": ["cuiaba", "cuiabá"]},
    {"value": "Várzea Grande", "state": "MT", "aliases": ["varzea grande", "várzea grande"]},
    {"value": "Campo Grande", "state": "MS", "aliases": ["campo grande"]},
    {"value": "Vitória", "state": "ES", "aliases": ["vitoria", "vitória"]},
    {"value": "Vila Velha", "state": "ES", "aliases": ["vila velha"]},
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
    "rio de janeiro": ["Centro", "Copacabana", "Ipanema", "Barra da Tijuca", "Tijuca", "Botafogo"],
    "belo horizonte": ["Centro", "Savassi", "Lourdes", "Pampulha", "Buritis"],
    "curitiba": ["Centro", "Batel", "Água Verde", "Boa Vista", "CIC"],
    "porto alegre": ["Centro", "Moinhos de Vento", "Cidade Baixa", "Menino Deus"],
    "salvador": ["Centro", "Pituba", "Barra", "Rio Vermelho", "Itapuã"],
    "recife": ["Boa Viagem", "Centro", "Casa Forte", "Pina"],
    "fortaleza": ["Aldeota", "Meireles", "Centro", "Parangaba"],
    "brasília": ["Asa Sul", "Asa Norte", "Taguatinga", "Ceilândia", "Águas Claras"],
}


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_text(value: str) -> str:
    text = _safe_text(value).lower()
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
    return " ".join(text.split())


def _term_matches(term: str, values: Iterable[str]) -> bool:
    raw_term = _normalize_text(term)
    if not raw_term:
        return True

    for value in values:
        normalized = _normalize_text(value)
        if normalized.startswith(raw_term) or raw_term in normalized:
            return True
    return False


def _build_item(value: str, field: str, subtitle: str = "", extra: dict | None = None) -> dict:
    payload = {
        "value": _safe_text(value),
        "label": _safe_text(value),
        "field": _safe_text(field),
        "subtitle": _safe_text(subtitle),
    }
    if extra:
        payload.update(extra)
    return payload


def _is_brazil_country(value: str) -> bool:
    return _normalize_text(value) in {"", "brasil", "brazil"}


def get_brazil_state_catalog() -> list[dict]:
    return [{"sigla": item["sigla"], "nome": item["nome"]} for item in BRAZIL_STATES]


def _get_state_items() -> list[dict]:
    items = []
    for state in BRAZIL_STATES:
        items.append(_build_item(state["sigla"], "estado", state["nome"], {"state_code": state["sigla"], "state_name": state["nome"]}))
        items.append(_build_item(state["nome"], "estado", state["sigla"], {"state_code": state["sigla"], "state_name": state["nome"]}))
    return items


def _state_matches(selected_state: str, state_code: str, state_name: str) -> bool:
    if not _safe_text(selected_state):
        return True
    normalized = _normalize_text(selected_state)
    return normalized in {_normalize_text(state_code), _normalize_text(state_name)}


def _get_city_state_label(state_code: str) -> str:
    for state in BRAZIL_STATES:
        if state["sigla"] == state_code:
            return f"{state['nome']} - {state['sigla']}"
    return state_code


def _get_neighborhood_city_label(city_norm_key: str) -> str:
    for city in BRAZIL_CITIES:
        if _normalize_text(city["value"]) == city_norm_key:
            return city["value"]
    return city_norm_key.title()


def _get_neighborhood_items(selected_city: str = "") -> list[dict]:
    city_norm = _normalize_text(selected_city)
    items = []

    if city_norm and city_norm in NEIGHBORHOODS_BY_CITY:
        city_label = _get_neighborhood_city_label(city_norm)
        for neighborhood in NEIGHBORHOODS_BY_CITY[city_norm]:
            items.append(_build_item(neighborhood, "bairro", city_label))
        return items

    for city_norm_key, neighborhoods in NEIGHBORHOODS_BY_CITY.items():
        city_label = _get_neighborhood_city_label(city_norm_key)
        for neighborhood in neighborhoods:
            items.append(_build_item(neighborhood, "bairro", city_label))

    return items


def get_region_suggestions(
    field: str,
    term: str = "",
    pais: str = "Brasil",
    estado: str = "",
    cidade: str = "",
    limit: int = 8,
) -> list[dict]:
    normalized_field = _normalize_text(field)

    if normalized_field == "pais":
        items = [
            _build_item("Brasil", "pais", "América do Sul"),
            _build_item("Argentina", "pais", "América do Sul"),
            _build_item("Paraguai", "pais", "América do Sul"),
            _build_item("Uruguai", "pais", "América do Sul"),
            _build_item("Chile", "pais", "América do Sul"),
            _build_item("Estados Unidos", "pais", "América do Norte"),
            _build_item("Portugal", "pais", "Europa"),
            _build_item("Espanha", "pais", "Europa"),
        ]
        filtered = [item for item in items if _term_matches(term, [item["value"], item["subtitle"]])]
        return filtered[:limit]

    if normalized_field == "estado":
        if not _is_brazil_country(pais):
            return []
        state_items = _get_state_items()
        filtered = [
            item for item in state_items
            if _term_matches(term, [item["value"], item["label"], item["subtitle"], item.get("state_name", "")])
        ]
        return filtered[:limit]

    if normalized_field == "cidade":
        if not _is_brazil_country(pais):
            return []
        filtered = []
        for city_item in BRAZIL_CITIES:
            if not _state_matches(estado, city_item["state"], next((x["nome"] for x in BRAZIL_STATES if x["sigla"] == city_item["state"]), city_item["state"])):
                continue
            if _term_matches(term, [city_item["value"], *city_item.get("aliases", [])]):
                filtered.append(_build_item(city_item["value"], "cidade", _get_city_state_label(city_item["state"])))
        return filtered[:limit]

    if normalized_field == "bairro":
        if not _is_brazil_country(pais):
            return []
        items = _get_neighborhood_items(selected_city=cidade)
        filtered = [item for item in items if _term_matches(term, [item["value"], item["subtitle"]])]
        dedup = []
        seen = set()
        for item in filtered:
            key = (_normalize_text(item["value"]), _normalize_text(item["subtitle"]))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)
        return dedup[:limit]

    return []
