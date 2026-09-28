import json

import httpx

from config import GROQ_API_KEY

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
WHISPER_MODEL = "whisper-large-v3-turbo"
CHAT_MODEL = "openai/gpt-oss-120b"

TRANSCRIBE_TIMEOUT = httpx.Timeout(connect=5, read=30, write=10, pool=5)
CHAT_TIMEOUT = httpx.Timeout(connect=5, read=20, write=10, pool=5)

SYSTEM_PROMPT = (
    "Tu es un expert en musique. On te donne la transcription approximative de paroles "
    "fredonnées ou chantées de mémoire, potentiellement pleine d'erreurs et d'onomatopées. "
    "Devine le titre et l'artiste les plus probables. Réponds UNIQUEMENT avec un objet JSON de "
    'la forme {"titre": "...", "artiste": "..."}. Si tu ne trouves vraiment pas, utilise "Inconnu".'
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
                data = {"model": WHISPER_MODEL, "response_format": "json"}
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
        "temperature": 0.2,
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
