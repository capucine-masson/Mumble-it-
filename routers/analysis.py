import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from config import UPLOAD_DIR
from database import get_db
from dependencies import get_current_pseudo
from models import RecordingOut
from serializers import row_to_recording_out
from services import deezer_client, groq_client

router = APIRouter(prefix="/recordings", tags=["analysis"])


@router.post("/{recording_id}/analyze", response_model=RecordingOut)
async def analyze_recording(
    recording_id: int,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT * FROM recordings WHERE id = ? AND pseudo = ?", (recording_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Fredonnement introuvable.")

    file_path = os.path.join(UPLOAD_DIR, row["filename"])
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Fichier audio introuvable.")

    db.execute(
        "UPDATE recordings SET analysis_status = 'pending', analysis_error = NULL WHERE id = ?",
        (recording_id,),
    )
    db.commit()

    try:
        transcript = await groq_client.transcribe_audio(file_path, row["original_mime"])
        db.execute("UPDATE recordings SET transcript = ? WHERE id = ?", (transcript, recording_id))
        db.commit()

        guess = await groq_client.guess_song(transcript)
        db.execute(
            "UPDATE recordings SET guessed_title = ?, guessed_artist = ? WHERE id = ?",
            (guess["titre"], guess["artiste"], recording_id),
        )
        db.commit()

        deezer_result = await deezer_client.search_track(guess["titre"], guess["artiste"])
        db.execute(
            "UPDATE recordings SET deezer_track_id = ?, deezer_link = ?, analysis_status = 'done' WHERE id = ?",
            (
                deezer_result["id"] if deezer_result else None,
                deezer_result["link"] if deezer_result else None,
                recording_id,
            ),
        )
        db.commit()
    except groq_client.GroqError as exc:
        db.execute(
            "UPDATE recordings SET analysis_status = 'error', analysis_error = ? WHERE id = ?",
            (str(exc), recording_id),
        )
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc))

    updated = db.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
    return row_to_recording_out(updated)
