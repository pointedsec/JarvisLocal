"""
web_search.py

Module for performing internet searches to provide up-to-date information.
Uses DuckDuckGo search via the duckduckgo-search library.
"""

import logging
from typing import List, Optional

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logging.warning("duckduckgo-search not installed. Web search disabled.")


# Keywords that suggest the query needs current/live information
CURRENT_INFO_KEYWORDS = [
    # Spanish - sports/results
    "resultado", "resultados", "marcador", "gol", "goles",
    "partido", "partidos", "clasificación", "jornada",
    "liga", "champions", "copa", "mundial",
    "fichaje", "fichajes", "traspaso", "traspasos",
    # Spanish - time-sensitive
    "ayer", "hoy", "anoche", "esta semana", "este fin de semana",
    "última hora", "últimas noticias", "ahora mismo",
    "reciente", "recientes", "actual", "actuales",
    # Spanish - general current events
    "noticias", "noticia", "qué pasó", "qué ha pasado",
    "cómo quedó", "cómo va", "cómo están", "quién ganó",
    "precio", "cotización", "bolsa", "tiempo", "clima",
    "elecciones", "estreno",
    # English equivalents
    "score", "result", "match", "game", "news",
    "yesterday", "today", "latest", "current",
    "who won", "how did", "what happened",
]

# Football-specific keywords for Manolo Lama mode
FOOTBALL_KEYWORDS = [
    # Spanish
    "fútbol", "futbol", "gol", "goles", "partido", "partidos",
    "liga", "champions", "copa del rey", "europa league",
    "selección", "seleccion", "mundial",
    "fichaje", "fichajes", "traspaso",
    "portero", "delantero", "centrocampista", "defensa",
    "penalti", "penalty", "tarjeta roja", "tarjeta amarilla",
    "fuera de juego", "córner", "corner",
    "entrenador", "míster", "mister", "banquillo",
    "clasificación", "clasificacion", "jornada", "descenso", "ascenso",
    # Team names
    "atlético", "atletico", "atleti", "colchonero", "colchoneros",
    "real madrid", "madrid", "merengue", "merengues", "madridista",
    "barcelona", "barça", "barca", "culé", "cules", "culés", "blaugrana",
    "sevilla", "betis", "valencia", "villarreal", "athletic",
    "real sociedad", "espanyol", "celta", "getafe", "osasuna",
    "mallorca", "rayo vallecano", "rayo", "alavés", "alaves",
    "girona", "las palmas", "cádiz", "cadiz", "almería", "almeria",
    "deportivo", "sporting", "zaragoza", "levante",
    # International teams/leagues
    "premier league", "serie a", "bundesliga", "ligue 1",
    "manchester", "liverpool", "chelsea", "arsenal",
    "juventus", "milan", "inter", "napoli",
    "bayern", "dortmund", "psg", "paris",
    "messi", "cristiano", "ronaldo", "mbappé", "mbappe",
    "haaland", "bellingham", "vinicius", "vinícius",
    "simeone", "ancelotti", "xavi", "flick",
    # English
    "football", "soccer", "goal", "goals",
    "striker", "goalkeeper", "midfielder",
]

# Manolo Lama style system prompt addition
MANOLO_LAMA_STYLE = (
    "IMPORTANTE: Para esta respuesta, DEBES responder imitando el estilo de "
    "Manolo Lama, el famoso comentarista deportivo español. Usa su estilo "
    "característico: apasionado, dramático, con expresiones como "
    "'¡GOOOOL!', '¡Increíble!', '¡Señores, esto es fútbol!', "
    "'¡No me lo puedo creer!', '¡Vaya jugada!', '¡Qué barbaridad!'. "
    "Sé entusiasta, usa muchas exclamaciones y transmite la emoción "
    "del fútbol en cada palabra. Habla como si estuvieras narrando "
    "un partido en directo."
)


def is_football_query(text: str) -> bool:
    """
    Detects if the user's query is about football/soccer.

    Args:
        text: The user's query text.

    Returns:
        True if the query is football-related.
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FOOTBALL_KEYWORDS)


def needs_web_search(text: str) -> bool:
    """
    Determines if the user's query likely needs current information
    from the internet.

    Args:
        text: The user's query text.

    Returns:
        True if the query likely needs a web search.
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CURRENT_INFO_KEYWORDS)


def web_search(query: str, max_results: int = 3, timeout: int = 10) -> Optional[List[dict]]:
    """
    Performs a web search using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
        timeout: Timeout in seconds for the search request.

    Returns:
        A list of result dicts with 'title', 'body', and 'href' keys,
        or None if the search fails or the library is not available.
    """
    if not DDGS_AVAILABLE:
        logging.warning("Web search unavailable: duckduckgo-search not installed.")
        return None

    try:
        logging.debug(f"Performing web search for: '{query}'")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, region="es-es"))

        if results:
            logging.debug(f"Web search returned {len(results)} results")
            return results
        else:
            logging.debug("Web search returned no results")
            return None

    except Exception as e:
        logging.error(f"Web search error: {e}")
        return None


def format_search_results(results: List[dict]) -> str:
    """
    Formats search results into a context string for the LLM.

    Args:
        results: List of result dicts from web_search().

    Returns:
        A formatted string with the search results.
    """
    if not results:
        return ""

    context_parts = ["[Resultados de búsqueda en internet]:"]
    for i, result in enumerate(results, 1):
        title = result.get("title", "Sin título")
        body = result.get("body", "Sin descripción")
        context_parts.append(f"{i}. {title}: {body}")

    return "\n".join(context_parts)
