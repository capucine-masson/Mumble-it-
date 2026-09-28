import sqlite3

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pseudo TEXT NOT NULL DEFAULT 'anonyme',
    filename TEXT NOT NULL,
    original_mime TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    transcript TEXT NULL,
    guessed_title TEXT NULL,
    guessed_artist TEXT NULL,
    analysis_status TEXT NOT NULL DEFAULT 'none' CHECK(analysis_status IN ('none','pending','done','error')),
    analysis_error TEXT NULL,
    deezer_track_id TEXT NULL,
    deezer_link TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_recordings_pseudo ON recordings(pseudo);
"""


def get_connection() -> sqlite3.Connection:
    # check_same_thread=False : FastAPI résout les dépendances synchrones dans un thread
    # de pool distinct du thread d'exécution des routes async ; la connexion créée par
    # get_db() doit donc pouvoir être utilisée depuis un autre thread que celui qui l'a ouverte.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
