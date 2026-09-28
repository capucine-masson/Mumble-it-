import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "mumble.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
