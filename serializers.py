import urllib.parse

from models import RecordingOut


def _youtube_link(title, artist):
    query = " ".join(part for part in [title, artist] if part)
    if not query:
        return None
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)


def _spotify_link(title, artist):
    query = " ".join(part for part in [title, artist] if part)
    if not query:
        return None
    return "https://open.spotify.com/search/" + urllib.parse.quote(query)


def row_to_recording_out(row) -> RecordingOut:
    data = dict(row)
    data.pop("folder_id", None)
    title = data.get("guessed_title")
    artist = data.get("guessed_artist")
    data["youtube_link"] = _youtube_link(title, artist)
    data["spotify_link"] = _spotify_link(title, artist)
    return RecordingOut(**data)
