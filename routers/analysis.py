import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from dependencies import get_current_pseudo
from models import RecordingOut
from serializers import row_to_recording_out
from services.analysis_service import run_analysis

router = APIRouter(prefix="/recordings", tags=["analysis"])


@router.post("/{recording_id}/analyze", response_model=RecordingOut)
async def analyze_recording(
    recording_id: int,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT id FROM recordings WHERE id = ? AND pseudo = ?", (recording_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Fredonnement introuvable.")

    await run_analysis(recording_id)

    updated = db.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
    if updated["analysis_status"] == "error":
        raise HTTPException(status_code=502, detail=updated["analysis_error"] or "Erreur d'analyse.")
    return row_to_recording_out(updated)
