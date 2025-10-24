## Buchfahrplan Generator

Interaktive Web-App zum Erstellen österreichischer/deutscher Buchfahrpläne. Das Backend basiert auf Flask und liefert sowohl ein minimalistisch-modernes UI als auch JSON-APIs, um Strecken, Fahrpläne und PDF-Exporte zu verwalten.

### Struktur

```
server/
  app.py              # Flask Entry-Point
  requirements.txt    # Python-Abhängigkeiten
  app/
    __init__.py       # Flask Factory & Blueprints
    models.py         # Route- & Fahrplanmodelle
    routes.py         # API-/HTML-Routen
    storage.py        # In-Memory-Datenhaltung & Beispielstrecken
    pdf.py            # PDF-Erzeugung mit reportlab
    templates/index.html
    static/css/style.css
    static/js/app.js
```

### Quickstart

1. Python-Umgebung aktivieren (optional) und Abhängigkeiten installieren:

   ```bash
   cd server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Server starten:

   ```bash
   flask --app app run
   ```

3. Browser öffnen: <http://127.0.0.1:5000>

### Mit Docker

```bash
docker compose up --build
```

Der Dienst lauscht standardmäßig auf Port `5000`. Über `PORT=8080 docker compose up` kann der externe Port überschrieben werden.

### Deployment mit Komodo

- Komodo erkennt das Projekt automatisch über die bereitgestellte `Dockerfile`.
- Setze in Komodo die Umgebungsvariable `PORT` (Standard `5000`), damit der Startbefehl `gunicorn --bind 0.0.0.0:$PORT app:app` den richtigen Port nutzt.
- Verwende das Compose-Target `app` oder stelle das Image direkt aus dem Dockerfile bereit.

### Aktuelle Features

- Zwei realitätsnahe Beispielstrecken (ÖBB Westbahn, MVV S3 München)
- Automatischer Grundfahrplan basierend auf Streckenkilometern & Durchschnittsgeschwindigkeit
- Bearbeitung von Ankunft/Abfahrt, Gleis und Bemerkungen im Browser
- Speichern über JSON-API & Download eines Buchfahrplans als PDF

### Ausblick

- Persistente Datenbank
- Import echter Streckendaten über ÖBB/DB Open-Data
- Mehr Layoutoptionen für PDF (verschiedene Buchfahrplan-Templates)
