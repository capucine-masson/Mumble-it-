import os
import sqlite3
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from config import UPLOAD_DIR
from database import get_db
from dependencies import get_current_pseudo
from models import RecordingFolderUpdate, RecordingOut
from serializers import row_to_recording_out

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
        "INSERT INTO recordings (pseudo, folder_id, filename, original_mime) VALUES (?, ?, ?, ?)",
        (pseudo, folder_id, filename, content_type),
    )
    db.commit()

    row = db.execute("SELECT * FROM recordings WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_recording_out(row)


@router.get("", response_model=list[RecordingOut])
def list_recordings(
    folder_id: Optional[int] = None,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    query = "SELECT * FROM recordings WHERE pseudo = ?"
    params: list = [pseudo]
    if folder_id is not None:
        query += " AND folder_id = ?"
        params.append(folder_id)
    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    return [row_to_recording_out(row) for row in rows]


@router.get("/{recording_id}", response_model=RecordingOut)
def get_recording(
    recording_id: int,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT * FROM recordings WHERE id = ? AND pseudo = ?", (recording_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Fredonnement introuvable.")
    return row_to_recording_out(row)


@router.get("/{recording_id}/audio")
def get_recording_audio(
    recording_id: int,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT filename, original_mime FROM recordings WHERE id = ? AND pseudo = ?",
        (recording_id, pseudo),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Fredonnement introuvable.")
    path = os.path.join(UPLOAD_DIR, row["filename"])
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Fichier audio introuvable.")
    return FileResponse(path, media_type=row["original_mime"])


@router.delete("/{recording_id}", status_code=204)
def delete_recording(
    recording_id: int,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT filename FROM recordings WHERE id = ? AND pseudo = ?", (recording_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Fredonnement introuvable.")

    db.execute("DELETE FROM recordings WHERE id = ? AND pseudo = ?", (recording_id, pseudo))
    db.commit()

    path = os.path.join(UPLOAD_DIR, row["filename"])
    if os.path.isfile(path):
        os.remove(path)


@router.put("/{recording_id}/folder", response_model=RecordingOut)
def update_recording_folder(
    recording_id: int,
    payload: RecordingFolderUpdate,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT id FROM recordings WHERE id = ? AND pseudo = ?", (recording_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Fredonnement introuvable.")

    if payload.folder_id is not None:
        folder_row = db.execute(
            "SELECT id FROM folders WHERE id = ? AND pseudo = ?", (payload.folder_id, pseudo)
        ).fetchone()
        if folder_row is None:
            raise HTTPException(status_code=404, detail="Dossier introuvable.")

    db.execute(
        "UPDATE recordings SET folder_id = ? WHERE id = ? AND pseudo = ?",
        (payload.folder_id, recording_id, pseudo),
    )
    db.commit()

    updated = db.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
    return row_to_recording_out(updated)
