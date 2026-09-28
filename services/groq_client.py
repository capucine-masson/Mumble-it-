import json

import httpx

from config import GROQ_API_KEY

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
WHISPER_MODEL = "whisper-large-v3-turbo"
CHAT_MODEL = "openai/gpt-oss-120b"

TRANSCRIBE_TIMEOUT = httpx.Timeout(connect=5, read=30, write=10, pool=5)
CHAT_TIMEOUT = httpx.Timeout(connect=5, read=20, write=10, pool=5)

SYSTEM_PROMPT = (
    "Tu es un expert en musique avec une culture encyclopédique : tubes internationaux, chansons "
    "traditionnelles, comptines, génériques, chansons pour enfants, musiques de film, etc.\n\n"
    "On te donne la transcription approximative de paroles fredonnées ou chantées de mémoire par "
    "quelqu'un qui ne se souvient plus exactement des mots ni du titre. Cette transcription peut "
    "être bruitée : erreurs de reconnaissance vocale, onomatopées répétées (na na na, la la la, "
    "lalala...), mots incomplets ou dans le désordre, texte très court.\n\n"
    "Ta mission : proposer la chanson la plus probable, même à partir d'indices faibles.\n\n"
    "Règles impératives :\n"
    "1. Fais TOUJOURS une hypothèse. \"Inconnu\" est un dernier recours, seulement si les paroles "
    "ne correspondent vraiment à aucune chanson imaginable — n'y recours presque jamais.\n"
    "2. Des onomatopées répétées (na na na, la la la, oh oh oh...) sont presque toujours le refrain "
    "d'une chanson célèbre : cherche activement à laquelle elles appartiennent au lieu de répondre "
    "Inconnu.\n"
    "3. Si les paroles correspondent à une chanson traditionnelle, une comptine ou un chant populaire "
    "sans auteur précis (par exemple 'Joyeux anniversaire', 'Au clair de la lune', 'Frère Jacques', "
    "'Happy Birthday to You'), donne son titre usuel et utilise \"Traditionnel\" comme artiste.\n"
    "4. Corrige mentalement les probables erreurs de transcription phonétique avant de conclure.\n"
    "5. Réponds UNIQUEMENT avec un objet JSON strict, sans aucun texte autour : "
    '{"titre": "...", "artiste": "..."}.\n\n'
    "Exemples :\n"
    'Paroles : "joyeux anniversaire joyeux anniversaire" -> '
    '{"titre": "Joyeux anniversaire", "artiste": "Traditionnel"}\n'
    'Paroles : "na na na na na na na na na na" -> '
    '{"titre": "Hey Jude", "artiste": "The Beatles"}\n'
    'Paroles : "despacito despacito" -> '
    '{"titre": "Despacito", "artiste": "Luis Fonsi"}'
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
