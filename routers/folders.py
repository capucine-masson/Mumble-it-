import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from dependencies import get_current_pseudo
from models import FolderCreate, FolderOut, FolderUpdate

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("", response_model=list[FolderOut])
def list_folders(
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    rows = db.execute(
        "SELECT id, name, created_at FROM folders WHERE pseudo = ? ORDER BY name", (pseudo,)
    ).fetchall()
    return [FolderOut(**dict(row)) for row in rows]


@router.post("", response_model=FolderOut, status_code=201)
def create_folder(
    payload: FolderCreate,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Le nom du dossier est requis.")
    try:
        cursor = db.execute("INSERT INTO folders (pseudo, name) VALUES (?, ?)", (pseudo, name))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Un dossier avec ce nom existe déjà.")
    row = db.execute(
        "SELECT id, name, created_at FROM folders WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return FolderOut(**dict(row))


@router.put("/{folder_id}", response_model=FolderOut)
def rename_folder(
    folder_id: int,
    payload: FolderUpdate,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Le nom du dossier est requis.")
    row = db.execute(
        "SELECT id FROM folders WHERE id = ? AND pseudo = ?", (folder_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Dossier introuvable.")
    try:
        db.execute(
            "UPDATE folders SET name = ? WHERE id = ? AND pseudo = ?", (name, folder_id, pseudo)
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Un dossier avec ce nom existe déjà.")
    updated = db.execute(
        "SELECT id, name, created_at FROM folders WHERE id = ?", (folder_id,)
    ).fetchone()
    return FolderOut(**dict(updated))


@router.delete("/{folder_id}", status_code=204)
def delete_folder(
    folder_id: int,
    pseudo: str = Depends(get_current_pseudo),
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT id FROM folders WHERE id = ? AND pseudo = ?", (folder_id, pseudo)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Dossier introuvable.")
    db.execute("DELETE FROM folders WHERE id = ? AND pseudo = ?", (folder_id, pseudo))
    db.commit()
