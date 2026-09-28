from typing import Optional

from pydantic import BaseModel


class RecordingOut(BaseModel):
    id: int
    pseudo: str
    filename: str
    created_at: str
    transcript: Optional[str] = None
    guessed_title: Optional[str] = None
    guessed_artist: Optional[str] = None
    analysis_status: str
    analysis_error: Optional[str] = None
    deezer_link: Optional[str] = None
    youtube_link: Optional[str] = None
    spotify_link: Optional[str] = None
