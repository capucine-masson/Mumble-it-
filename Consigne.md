Je veux construire une web app "Mumble It" : Tu as un son en tête mais pas les mots exacts, ni le titre. Tu chantes ce dont tu te souviens, l'app transcrit ta voix et demande à une IA de deviner la chanson à partir de ces paroles approximatives - avec le lien d'écoute Deezer à la clé.

Stack imposée (minimale exprès) :
- Backend : Python + FastAPI, lancé en local avec `uvicorn main:app --reload`
- Persistance : SQLite, accès direct
- Frontend : HTML/Jinja2 + JS minimal (pas de framework JS)
- Secrets : clé API Groq dans un `.env` chargé via python-dotenv, `.env` dans le .gitignore. Pas besoin de validation stricte au démarrage, juste ne jamais la mettre en dur dans le code.

Contrainte de méthode : ne code rien avant d'avoir proposé un découpage en étapes. Priorité stricte, dans cet ordre :

1. V0 : Squelette FastAPI + SQLite + .env
2. V1 : Enregistrement de notre fredonnement lorsqu'on appuie sur le gros logo shazam bis qui sera placé au milieu de l'écran
3. V1 : Possibilité de réécouter - supprimer ranger dans dossiers - notre fredonnement
4. V2 : Analyse de l'enregistrement par un LLM (clé API GROQ) qui a pour but de retrouver la musique (chanteur + titre) deux appels Groq séparés, chacun avec une responsabilité unique.
4.1 : Appel 1 - Transcription : POST du fichier audio vers l'endpoint Whisper de Groq (whisper-large-v3 ou la variante turbo), qui te renvoie du texte brut.
4.2 : Appel 2 - Devinette : ce texte transcrit part dans un prompt vers un modèle de chat Groq (ex: llama-3.3-70b-versatile), avec une instruction du type "Voici des paroles approximatives fredonnées, devine le titre et l'artiste, réponds en JSON structuré {titre, artiste}".
5. V3 : Donne avec ça le lien de la chanson sur deezer (Deezer a une API publique de recherche) et un lien de recherche youtube, quand on clique dessus on est directement redirigé vers la page youtube ou le son deezer
6. V4 : Login factice - juste un champ pseudo en session/localStorage sans vraie auth

Contraintes visuelles :
Je veux une app fancy qui catch avec ces tons de couleurs :
390099
9E0059
FF0054
FF5400
Ces polices :
titre : https://coolors.co/font/alfa-slab-one
corps : https://coolors.co/font/alata
notes pour qqs mots/bouts de phrases : https://coolors.co/font/alex-brush

Méthode d'exécution :
- Après ton découpage en étapes, attends ma validation avant de coder.
- Pour chaque étape : fais un résumé technique de ce qui a été fait (routes, tables, etc etc)

Contraintes de sécurité et qualité par défaut (à respecter sans que je le redemande) :
- Actions qui modifient l'état (create/update/delete) en POST/PUT/DELETE, jamais en GET
- Pas d'innerHTML non échappé côté JS
- Si un appel LLM coûte cher ou peut créer un doublon (ex: double-clic), une protection simple suffit (désactiver le bouton pendant l'appel)
- N'oublie pas les time out et injection sql doit etre impossible