import urllib.parse

from models import RecordingOut


def _youtube_link(title, artist):
    query = " ".join(part for part in [title, artist] if part)
    if not query:
        return None
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)


def row_to_recording_out(row) -> RecordingOut:
    data = dict(row)
    data["youtube_link"] = _youtube_link(data.get("guessed_title"), data.get("guessed_artist"))
    return RecordingOut(**data)
