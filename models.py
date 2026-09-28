from typing import Optional

from pydantic import BaseModel


class FolderCreate(BaseModel):
    name: str


class FolderUpdate(BaseModel):
    name: str


class FolderOut(BaseModel):
    id: int
    name: str
    created_at: str


class RecordingFolderUpdate(BaseModel):
    folder_id: Optional[int] = None


class RecordingOut(BaseModel):
    id: int
    pseudo: str
    folder_id: Optional[int]
    filename: str
    created_at: str
    transcript: Optional[str] = None
    guessed_title: Optional[str] = None
    guessed_artist: Optional[str] = None
    analysis_status: str
    analysis_error: Optional[str] = None
    deezer_link: Optional[str] = None
    youtube_link: Optional[str] = None
