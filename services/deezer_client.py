from typing import Optional

import httpx

DEEZER_SEARCH_URL = "https://api.deezer.com/search"
DEEZER_TIMEOUT = httpx.Timeout(8)


async def search_track(titre: str, artiste: str) -> Optional[dict]:
    query = " ".join(part for part in [titre, artiste] if part and part.lower() != "inconnu").strip()
    if not query:
        return None

    try:
        async with httpx.AsyncClient(timeout=DEEZER_TIMEOUT) as client:
            response = await client.get(DEEZER_SEARCH_URL, params={"q": query})
    except httpx.HTTPError:
        return None

    if response.status_code != 200:
        return None

    payload = response.json()
    results = payload.get("data") or []
    if not results:
        return None

    track = results[0]
    return {"id": str(track.get("id")), "link": track.get("link")}
