from typing import Optional

from fastapi import Header


def get_current_pseudo(x_mumble_pseudo: Optional[str] = Header(default=None)) -> str:
    return x_mumble_pseudo.strip() if x_mumble_pseudo and x_mumble_pseudo.strip() else "anonyme"
