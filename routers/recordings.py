import os
import sqlite3
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from config import UPLOAD_DIR
from database import get_db
from dependencies import get_current_pseudo
from models import RecordingOut
from serializers import row_to_recording_out
from services.analysis_service import run_analysis

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
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    content_type = (audio.content_type or "").lower()
    if not content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Le fichier envoyé n'est pas un fichier audio.")

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier audio vide.")

    extension = _extension_for(content_type)
    filename = f"{uuid.uuid4().hex}.{extension}"
    destination = os.path.join(UPLOAD_DIR, filename)
    with open(destination, "wb") as f:
        f.write(data)

    cursor = db.execute(
        "INSERT INTO recordings (pseudo, filename, original_mime) VALUES (?, ?, ?)",
        (pseudo, filename, content_type),
    )
    db.commit()

    recording_id = cursor.lastrowid
    background_tasks.add_task(run_analysis, recording_id)

    row = db.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
    return row_to_recording_out(row)


@router.get("", response_model=list[RecordingOut])
def list_recordings(
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    rows = db.execute(
        "SELECT * FROM recordings WHERE pseudo = ? ORDER BY created_at DESC", (pseudo,)
    ).fetchall()
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
