# ABoroOffice

Modulares Enterprise-Management-System auf Basis von Django & PostgreSQL.

## Features

- **ERP** - Auftraege, Rechnungen, Angebote, Mahnwesen, Wareneingang, Veranstaltungen, Preiskalkulation
- **CRM** - Kundenverwaltung und Kontaktmanagement
- **HelpDesk** - Ticketsystem mit KI-Unterstuetzung (Ollama/Claude/OpenAI)
- **Personal** - Externe & interne Mitarbeiter, Zeiterfassung, Lohnexport, Skills-Verwaltung
- **Finanzbuchhaltung** - FiBu-Modul
- **Vertraege** - Vertragsverwaltung
- **Marketing** - Kampagnen-Management
- **Projekte** - Projektverwaltung
- **Cloud Storage** - Dateiverwaltung mit Benutzer-Authentifizierung
- **Classroom** - Mobiles Klassenzimmer-Management
- **Workflows & Freigaben** - Genehmigungsprozesse
- **Plugin-System** - Erweiterbar durch Plugins
- **REST API** - Vollstaendige API fuer alle Module
- **Admin-Dashboard** - Systemeinstellungen, Dark Mode, Theming

## Schnellstart

```bash
# 1. docker-compose.yml und .env herunterladen
# 2. .env anpassen (Datenbank-Passwoerter etc.)
# 3. Starten:
docker compose up -d

# 4. Datenbank-Migrationen ausfuehren:
docker compose exec web python manage.py migrate

# 5. Admin-Benutzer erstellen:
docker compose exec web python manage.py createsuperuser
```

## docker-compose.yml (Beispiel)

```yaml
services:
  web:
    image: aboro181172/aborooffice:latest
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - ALLOWED_HOSTS=*
      - DATABASE_HOST=db
      - DATABASE_PORT=5432
      - DATABASE_NAME=aboro_db
      - DATABASE_USER=aboro_user
      - DATABASE_PASSWORD=sicheres_passwort
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    volumes:
      - media_data:/app/media
      - static_data:/app/staticfiles
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=aboro_db
      - POSTGRES_USER=aboro_user
      - POSTGRES_PASSWORD=sicheres_passwort
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aboro_user -d aboro_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  celery:
    image: aboro181172/aborooffice:latest
    command: celery -A config worker -l info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_HOST=db
      - DATABASE_PORT=5432
      - DATABASE_NAME=aboro_db
      - DATABASE_USER=aboro_user
      - DATABASE_PASSWORD=sicheres_passwort
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    image: aboro181172/aborooffice:latest
    command: celery -A config beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_HOST=db
      - DATABASE_PORT=5432
      - DATABASE_NAME=aboro_db
      - DATABASE_USER=aboro_user
      - DATABASE_PASSWORD=sicheres_passwort
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  media_data:
  static_data:
```

## Umgebungsvariablen

| Variable | Beschreibung | Standard |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Settings-Modul | `config.settings.production` |
| `ALLOWED_HOSTS` | Erlaubte Hosts | `*` |
| `DATABASE_HOST` | PostgreSQL Host | `db` |
| `DATABASE_PORT` | PostgreSQL Port | `5432` |
| `DATABASE_NAME` | Datenbankname | `aboro_db` |
| `DATABASE_USER` | DB-Benutzer | `aboro_user` |
| `DATABASE_PASSWORD` | DB-Passwort | - |
| `REDIS_URL` | Redis-URL | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery Broker | `redis://redis:6379/1` |
| `SECRET_KEY` | Django Secret Key | - |

## Technologie-Stack

- **Backend:** Python 3.12, Django 6
- **Datenbank:** PostgreSQL 16
- **Cache/Queue:** Redis 7, Celery
- **Frontend:** Bootstrap 5, Font Awesome
- **KI-Integration:** Ollama, Claude, OpenAI (optional)

## Ports

| Service | Port |
|---|---|
| Web | 8000 |
| PostgreSQL | 5432 (intern) |
| Redis | 6379 (intern) |

## Lizenz

Proprietaer - Alle Rechte vorbehalten.
