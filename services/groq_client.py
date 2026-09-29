import json

import httpx

from config import GROQ_API_KEY, TAVILY_API_KEY

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
WHISPER_MODEL = "whisper-large-v3-turbo"
CHAT_MODEL = "openai/gpt-oss-120b"

TRANSCRIBE_TIMEOUT = httpx.Timeout(connect=5, read=30, write=10, pool=5)
CHAT_TIMEOUT = httpx.Timeout(connect=5, read=20, write=10, pool=5)
TAVILY_TIMEOUT = httpx.Timeout(connect=5, read=20, write=10, pool=5)

SYSTEM_PROMPT = (
    "Tu es un expert en musique avec une culture encyclopédique : tubes internationaux, chansons "
    "traditionnelles, comptines, génériques, chansons pour enfants, musiques de film, etc.\n\n"
    "On te donne la transcription approximative de paroles fredonnées ou chantées de mémoire par "
    "quelqu'un qui ne se souvient plus exactement des mots ni du titre. Cette transcription peut "
    "être bruitée : erreurs de reconnaissance vocale, onomatopées répétées (na na na, la la la, "
    "lalala...), mots incomplets ou dans le désordre, texte très court.\n\n"
    "Ta mission : identifier la vraie chanson quand c'est possible, SANS JAMAIS inventer un titre "
    "ou un artiste qui n'existe pas réellement. Une fausse réponse qui a l'air plausible est PIRE "
    "qu'un \"Inconnu\" honnête : l'utilisateur va cliquer sur des liens d'écoute qui mèneront vers "
    "la mauvaise chanson.\n\n"
    "Distingue deux cas très différents :\n\n"
    "CAS 1 — Onomatopées ou refrain répété (na na na, la la la, oh oh, lalala...) : ce sont "
    "presque toujours des refrains de chansons célèbres. Cherche activement à laquelle ce refrain "
    "appartient et propose ta meilleure hypothèse même si tu n'es pas sûr à 100 %.\n\n"
    "CAS 2 — Paroles complètes avec un vrai sens (une phrase, une histoire, des mots précis) : "
    "dans ce cas, ne propose un titre et un artiste QUE SI tu reconnais réellement et précisément "
    "cette chanson (paroles quasi identiques dont tu es sûr qu'elles existent). Si les paroles ne "
    "correspondent à aucune chanson que tu reconnais avec certitude, réponds \"Inconnu\" — même si "
    "tu pourrais imaginer un titre et un artiste plausibles. NE FABRIQUE JAMAIS une chanson qui "
    "pourrait ne pas exister juste pour éviter de répondre Inconnu.\n\n"
    "Autres règles :\n"
    "- Si les paroles correspondent à une chanson traditionnelle, une comptine ou un chant populaire "
    "sans auteur précis (par exemple 'Joyeux anniversaire', 'Au clair de la lune', 'Frère Jacques', "
    "'Happy Birthday to You'), donne son titre usuel et utilise \"Traditionnel\" comme artiste.\n"
    "- Corrige mentalement les probables erreurs de transcription phonétique avant de conclure.\n"
    "- Réponds UNIQUEMENT avec un objet JSON strict, sans aucun texte autour : "
    '{"titre": "...", "artiste": "..."}.\n\n'
    "Exemples :\n"
    'Paroles : "joyeux anniversaire joyeux anniversaire" (CAS 1, refrain connu) -> '
    '{"titre": "Joyeux anniversaire", "artiste": "Traditionnel"}\n'
    'Paroles : "na na na na na na na na na na" (CAS 1, refrain connu) -> '
    '{"titre": "Hey Jude", "artiste": "The Beatles"}\n'
    'Paroles : "despacito despacito" (CAS 1, refrain connu) -> '
    '{"titre": "Despacito", "artiste": "Luis Fonsi"}\n'
    'Paroles : "une phrase originale et précise que tu ne reconnais pas avec certitude" '
    '(CAS 2, pas de reconnaissance fiable) -> {"titre": "Inconnu", "artiste": "Inconnu"}'
)

# Utilisé uniquement en fallback quand SYSTEM_PROMPT n'a rien trouvé : la chanson peut être
# trop récente pour faire partie des connaissances d'entraînement du modèle, d'où le besoin
# d'une recherche web explicite avant de conclure.
WEB_SYSTEM_PROMPT = (
    "Tu es un expert en musique. On te donne la transcription approximative de paroles "
    "fredonnées ou chantées de mémoire par quelqu'un qui ne se souvient plus exactement des "
    "mots ni du titre, accompagnée de résultats de recherche web (titres de pages et extraits) "
    "obtenus en cherchant ces paroles sur internet. Un premier passage sans recherche n'a rien "
    "trouvé : la chanson est peut-être trop récente pour faire partie des connaissances d'un "
    "modèle de langage, ou trop peu connue.\n\n"
    "Analyse les résultats de recherche fournis pour essayer d'identifier la vraie chanson, en "
    "tenant compte des probables erreurs de transcription phonétique dans les paroles.\n\n"
    "Règle absolue : ne renvoie un titre et un artiste QUE SI les résultats de recherche "
    "confirment clairement l'existence de cette chanson avec des paroles correspondantes. "
    "Une fausse réponse plausible est PIRE qu'un \"Inconnu\" honnête. Si les résultats ne "
    "confirment rien avec certitude (résultats non pertinents, contradictoires, ou absents), "
    "réponds \"Inconnu\". Ne te base jamais sur tes seules connaissances internes ici : seuls "
    "les résultats de recherche fournis comptent.\n\n"
    "Réponds UNIQUEMENT avec un objet JSON strict, sans aucun texte autour : "
    '{"titre": "...", "artiste": "..."}.'
)


class GroqError(Exception):
    pass


def _require_api_key() -> str:
    if not GROQ_API_KEY:
        raise GroqError("Clé Groq manquante : configure GROQ_API_KEY dans le fichier .env.")
    return GROQ_API_KEY


async def transcribe_audio(file_path: str, mime_type: str) -> str:
    api_key = _require_api_key()
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=TRANSCRIBE_TIMEOUT) as client:
            with open(file_path, "rb") as f:
                files = {"file": (file_path, f, mime_type or "application/octet-stream")}
                data = {"model": WHISPER_MODEL, "response_format": "json", "temperature": 0}
                response = await client.post(
                    f"{GROQ_BASE_URL}/audio/transcriptions", headers=headers, files=files, data=data
                )
    except httpx.TimeoutException as exc:
        raise GroqError("Le service de transcription Groq n'a pas répondu à temps.") from exc
    except httpx.HTTPError as exc:
        raise GroqError("Impossible de contacter le service de transcription Groq.") from exc

    if response.status_code != 200:
        raise GroqError(f"Erreur Groq lors de la transcription (code {response.status_code}).")

    payload = response.json()
    text = (payload.get("text") or "").strip()
    if not text:
        raise GroqError("La transcription est vide, impossible de deviner la chanson.")
    return text


async def guess_song(transcript: str) -> dict:
    api_key = _require_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": CHAT_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            response = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=body)
    except httpx.TimeoutException as exc:
        raise GroqError("Le service de suggestion Groq n'a pas répondu à temps.") from exc
    except httpx.HTTPError as exc:
        raise GroqError("Impossible de contacter le service de suggestion Groq.") from exc

    if response.status_code != 200:
        raise GroqError(f"Erreur Groq lors de la devinette (code {response.status_code}).")

    payload = response.json()
    try:
        content = payload["choices"][0]["message"]["content"]
        guess = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise GroqError("Réponse de Groq illisible.") from exc

    return {
        "titre": (guess.get("titre") or "Inconnu").strip() or "Inconnu",
        "artiste": (guess.get("artiste") or "Inconnu").strip() or "Inconnu",
    }


def _require_tavily_key() -> str:
    if not TAVILY_API_KEY:
        raise GroqError("Clé Tavily manquante : configure TAVILY_API_KEY dans le fichier .env.")
    return TAVILY_API_KEY


async def _tavily_search(query: str) -> list[dict]:
    api_key = _require_tavily_key()
    body = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 5,
        "include_answer": False,
    }

    try:
        async with httpx.AsyncClient(timeout=TAVILY_TIMEOUT) as client:
            response = await client.post(TAVILY_SEARCH_URL, json=body)
    except httpx.TimeoutException as exc:
        raise GroqError("Le service de recherche web Tavily n'a pas répondu à temps.") from exc
    except httpx.HTTPError as exc:
        raise GroqError("Impossible de contacter le service de recherche web Tavily.") from exc

    if response.status_code != 200:
        raise GroqError(f"Erreur Tavily lors de la recherche web (code {response.status_code}).")

    payload = response.json()
    return payload.get("results") or []


async def guess_song_web(transcript: str) -> dict:
    """Fallback avec recherche web (Tavily + gpt-oss-120b), pour les chansons trop récentes
    pour être connues du modèle utilisé par guess_song()."""
    results = await _tavily_search(f'lyrics "{transcript}"')
    if not results:
        return {"titre": "Inconnu", "artiste": "Inconnu"}

    search_context = "\n\n".join(
        f"- {r.get('title', '')}\n{(r.get('content') or '')[:500]}" for r in results
    )
    user_content = (
        f"Paroles transcrites : \"{transcript}\"\n\n"
        f"Résultats de recherche web :\n{search_context}"
    )

    api_key = _require_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": CHAT_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": WEB_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            response = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=body)
    except httpx.TimeoutException as exc:
        raise GroqError("Le service de suggestion Groq n'a pas répondu à temps.") from exc
    except httpx.HTTPError as exc:
        raise GroqError("Impossible de contacter le service de suggestion Groq.") from exc

    if response.status_code != 200:
        raise GroqError(f"Erreur Groq lors de la recherche web (code {response.status_code}).")

    payload = response.json()
    try:
        content = payload["choices"][0]["message"]["content"]
        guess = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise GroqError("Réponse de Groq (recherche web) illisible.") from exc

    return {
        "titre": (guess.get("titre") or "Inconnu").strip() or "Inconnu",
        "artiste": (guess.get("artiste") or "Inconnu").strip() or "Inconnu",
    }
