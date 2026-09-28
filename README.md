# 🎤 Mumble It

Tu as un son en tête, mais ni les paroles exactes ni le titre ? **Chante ou fredonne comme tu peux**, Mumble It transcrit ta voix, envoie ça à une IA qui devine le titre et l'artiste, et te renvoie directement le lien pour écouter le vrai morceau sur Deezer ou YouTube.

## Fonctionnalités

- 🎙️ **Enregistrement vocal** directement depuis le navigateur, en appuyant sur le gros logo au centre de l'écran
- 🔁 **Réécoute et gestion** de ses fredonnements (bibliothèque personnelle, suppression)
- 🧠 **Analyse IA en deux temps** via l'API Groq :
  1. Transcription audio → texte (Whisper)
  2. Devinette titre + artiste à partir du texte (LLM, réponse JSON structurée)
- 🔗 **Liens d'écoute automatiques** vers Deezer (API publique) et recherche YouTube
- 👤 **Pseudo factice** (pas de vraie authentification) pour retrouver ses propres fredonnements

## Lancer le projet

### 1. Prérequis
- Python 3.10+
- Une clé API [Groq](https://console.groq.com/)

### 2. Installation
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configuration
Copier `.env.example` en `.env` et renseigner ta clé :
```
GROQ_API_KEY=ta_cle_groq_ici
```

### 4. Démarrage
```bash
uvicorn main:app --reload
```
L'application est accessible sur `http://127.0.0.1:8000`.

## Choix techniques

- **Backend minimal** : FastAPI + accès SQLite direct (pas d'ORM), pour rester simple et lisible
- **Frontend sans framework** : HTML/Jinja2 + JS vanilla, découpé par responsabilité (`recorder.js`, `analysis.js`, `library.js`, `api.js`...)
- **Secrets hors code** : clé Groq chargée via `python-dotenv`, `.env` ignoré par git
- **Sécurité par défaut** : requêtes SQL paramétrées (pas d'injection possible), actions d'écriture en POST/DELETE uniquement, timeouts sur tous les appels externes (Groq, Deezer)
- **Analyse asynchrone** : lancée en tâche de fond (`BackgroundTasks`) pour ne pas bloquer l'upload de l'enregistrement

## Architecture

```
main.py                 → point d'entrée FastAPI, montage des routers et fichiers statiques
config.py               → chemins et variables d'environnement
database.py             → connexion SQLite, schéma, init
dependencies.py         → résolution du pseudo courant (login factice)
models.py               → schémas Pydantic (réponses API)
serializers.py          → conversion lignes SQLite → modèles

routers/
  pages.py              → pages HTML (accueil, bibliothèque)
  recordings.py         → CRUD des enregistrements audio
  analysis.py           → déclenchement de l'analyse IA

services/
  groq_client.py        → appels Groq (transcription Whisper + devinette LLM)
  deezer_client.py       → recherche du morceau sur Deezer
  analysis_service.py    → orchestration transcription → devinette → lien Deezer

static/                 → CSS et JS (enregistrement, lecture, bibliothèque)
templates/              → pages Jinja2
data/                   → base SQLite + fichiers audio uploadés
```

**Flux d'une analyse :**
`Enregistrement audio` → `POST /recordings` → tâche de fond → Groq Whisper (transcription) → Groq Chat (devinette titre/artiste) → Deezer (lien d'écoute) → mise à jour en base → consultable via `GET /recordings/{id}`.

## Aperçu

*(à venir — captures d'écran de l'interface)*
