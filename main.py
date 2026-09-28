import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import UPLOAD_DIR
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="Mumble It", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
