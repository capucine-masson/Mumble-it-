from typing import Optional

from fastapi import Header, Query


def get_current_pseudo(
    x_mumble_pseudo: Optional[str] = Header(default=None),
    pseudo: Optional[str] = Query(default=None),
) -> str:
    """Le pseudo vient normalement du header X-Mumble-Pseudo (envoyé par apiFetch), mais un
    élément <audio>/<img> ne peut pas fixer de header personnalisé sur sa requête : pour ces
    cas (ex: lecture audio), on accepte aussi le pseudo en paramètre de requête ?pseudo=."""
    value = x_mumble_pseudo or pseudo
    return value.strip() if value and value.strip() else "anonyme"
