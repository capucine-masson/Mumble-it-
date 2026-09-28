from typing import Optional

from pydantic import BaseModel


class RecordingOut(BaseModel):
    id: int
    pseudo: str
    folder_id: Optional[int]
    filename: str
    created_at: str
    analysis_status: str
