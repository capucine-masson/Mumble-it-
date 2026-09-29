import os

from config import ENABLE_WEB_FALLBACK, UPLOAD_DIR
from database import get_connection
from services import deezer_client, groq_client


async def run_analysis(recording_id: int) -> None:
    """Exécute le pipeline complet (transcription -> devinette -> Deezer) pour un fredonnement.

    Ouvre sa propre connexion SQLite : cette fonction est appelée aussi bien en tâche de
    fond (après la réponse HTTP d'upload) que dans une requête classique (réessai manuel),
    donc elle ne peut pas réutiliser une connexion liée au cycle de vie d'une autre requête.
    """
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,)).fetchone()
        if row is None:
            return

        file_path = os.path.join(UPLOAD_DIR, row["filename"])
        if not os.path.isfile(file_path):
            conn.execute(
                "UPDATE recordings SET analysis_status = 'error', analysis_error = ? WHERE id = ?",
                ("Fichier audio introuvable.", recording_id),
            )
            conn.commit()
            return

        conn.execute(
            "UPDATE recordings SET analysis_status = 'pending', analysis_error = NULL WHERE id = ?",
            (recording_id,),
        )
        conn.commit()

        try:
            transcript = await groq_client.transcribe_audio(file_path, row["original_mime"])
            conn.execute("UPDATE recordings SET transcript = ? WHERE id = ?", (transcript, recording_id))
            conn.commit()

            # On ne peut pas se fier à guess_song() (sans recherche) pour savoir s'il se
            # trompe : il peut halluciner un titre plausible avec la même assurance qu'une
            # vraie bonne réponse, sans jamais répondre "Inconnu" dans ce cas. La recherche
            # web (ancrée sur de vraies paroles trouvées en ligne) est donc utilisée en
            # priorité ; le LLM seul ne sert plus que de repli si le web est indisponible.
            guess = None
            if ENABLE_WEB_FALLBACK:
                try:
                    guess = await groq_client.guess_song_web(transcript)
                except groq_client.GroqError:
                    guess = None
            if guess is None:
                guess = await groq_client.guess_song(transcript)
            conn.execute(
                "UPDATE recordings SET guessed_title = ?, guessed_artist = ? WHERE id = ?",
                (guess["titre"], guess["artiste"], recording_id),
            )
            conn.commit()

            deezer_result = await deezer_client.search_track(guess["titre"], guess["artiste"])
            conn.execute(
                "UPDATE recordings SET deezer_track_id = ?, deezer_link = ?, analysis_status = 'done' WHERE id = ?",
                (
                    deezer_result["id"] if deezer_result else None,
                    deezer_result["link"] if deezer_result else None,
                    recording_id,
                ),
            )
            conn.commit()
        except groq_client.GroqError as exc:
            conn.execute(
                "UPDATE recordings SET analysis_status = 'error', analysis_error = ? WHERE id = ?",
                (str(exc), recording_id),
            )
            conn.commit()
    finally:
        conn.close()
