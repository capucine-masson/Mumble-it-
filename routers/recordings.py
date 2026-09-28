import os
import sqlite3
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from config import UPLOAD_DIR
from database import get_db
from dependencies import get_current_pseudo
from models import RecordingOut

router = APIRouter(prefix="/recordings", tags=["recordings"])

ALLOWED_EXTENSIONS = {
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}


def _extension_for(mime_type: str) -> str:
    base = mime_type.split(";")[0].strip().lower()
    return ALLOWED_EXTENSIONS.get(base, "webm")


@router.post("", response_model=RecordingOut, status_code=201)
async def create_recording(
    audio: UploadFile = File(...),
    folder_id: Optional[int] = Form(default=None),
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    content_type = (audio.content_type or "").lower()
    if not content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Le fichier envoyé n'est pas un fichier audio.")

    if folder_id is not None:
        folder_row = db.execute(
            "SELECT id FROM folders WHERE id = ? AND pseudo = ?", (folder_id, pseudo)
        ).fetchone()
        if folder_row is None:
            raise HTTPException(status_code=404, detail="Dossier introuvable.")

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier audio vide.")

    extension = _extension_for(content_type)
    filename = f"{uuid.uuid4().hex}.{extension}"
    destination = os.path.join(UPLOAD_DIR, filename)
    with open(destination, "wb") as f:
        f.write(data)

    cursor = db.execute(
        """
        INSERT INTO recordings (pseudo, folder_id, filename, original_mime)
        VALUES (?, ?, ?, ?)
        """,
        (pseudo, folder_id, filename, content_type),
    )
    db.commit()

    row = db.execute(
        "SELECT id, pseudo, folder_id, filename, created_at, analysis_status FROM recordings WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return RecordingOut(**dict(row))
