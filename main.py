import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import UPLOAD_DIR
from database import init_db
from routers import analysis, pages, recordings


class NoCacheStaticFiles(StaticFiles):
    """Empêche le navigateur de mettre en cache les fichiers statiques (JS/CSS/img).

    En dev, --reload recharge le backend à chaque modification, mais le navigateur
    gardait parfois une ancienne version d'un fichier JS/CSS en cache mémoire et ne
    revalidait jamais avec le serveur, donnant l'impression que les changements
    n'étaient pas pris en compte. Cache-Control: no-store force une requête réseau
    à chaque chargement de page.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="Mumble It", lifespan=lifespan)
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")
app.include_router(pages.router)
app.include_router(recordings.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
