# ABoroOffice

Modulares Enterprise-Management-System mit ERP, CRM, HelpDesk, Cloud-Storage und Veranstaltungsmanagement.

## Schnellstart

### Windows 11

```bash
# Virtual Environment erstellen
python -m venv .venv
.venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements-windows.txt

# Datenbank erstellen
python manage.py migrate

# Admin-Benutzer erstellen
python manage.py createsuperuser

# Server starten
python manage.py runserver
```

### Linux

```bash
# Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements-linux.txt

# Datenbank erstellen
python manage.py migrate

# Admin-Benutzer erstellen
python manage.py createsuperuser

# Server starten
python manage.py runserver
```

Server läuft unter: http://localhost:8000

---

## Projektstruktur

```
ABoroOffice/
├── apps/
│   ├── core/                 # Basis-Authentifizierung
│   ├── licensing/            # Lizenzsystem
│   ├── erp/                  # ERP (Aufträge, Rechnungen, Veranstaltungen)
│   ├── crm/                  # CRM (Leads, Opportunities, Accounts)
│   ├── helpdesk/             # Ticket-System, Chat, Knowledge Base
│   ├── cloude/               # Cloud-Speicher & Plugins
│   ├── personnel/            # Personalverwaltung & Externe Mitarbeiter
│   ├── contracts/            # Vertragsmanagement
│   ├── fibu/                 # Finanzbuchhaltung
│   ├── marketing/            # Marketing-Kampagnen
│   └── workflows/            # Workflow-Automatisierung
│
├── config/
│   ├── settings/
│   │   ├── base.py           # Gemeinsame Einstellungen
│   │   ├── development.py    # Entwicklung
│   │   └── production.py     # Produktion
│   ├── urls.py
│   └── wsgi.py
│
├── templates/                # Django Templates
├── static/                   # Statische Dateien
├── docs/                     # API-Dokumentation
└── tests/                    # Pytest Tests
```

---

## Module

| Modul | Beschreibung | URL |
|-------|--------------|-----|
| **ERP** | Aufträge, Rechnungen, Produkte, Veranstaltungen | `/erp/` |
| **CRM** | Leads, Opportunities, Accounts, Kampagnen | `/crm/` |
| **HelpDesk** | Tickets, Chat, Knowledge Base, AI-Support | `/helpdesk/` |
| **Cloude** | Cloud-Speicher, Sharing, Plugins | `/cloudstorage/` |
| **Personnel** | Mitarbeiter, Externe MA, Zeiterfassung | `/personnel/` |
| **Contracts** | Verträge, Rahmenverträge | `/contracts/` |
| **FiBu** | Finanzbuchhaltung, Konten | `/fibu/` |

---

## Konfiguration

### Umgebungsvariablen (.env)

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# E-Mail (optional)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=user@example.com
EMAIL_HOST_PASSWORD=password

# AWS Bedrock (optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Requirements-Dateien

| Datei | Verwendung |
|-------|------------|
| `requirements-windows.txt` | Windows-Entwicklung (pydantic 1.x) |
| `requirements-linux.txt` | Linux-Produktion (pydantic 2.x) |
| `requirements.txt` | Referenz (nicht direkt installieren) |

---

## Häufige Befehle

### Datenbank

```bash
python manage.py makemigrations    # Migrationen erstellen
python manage.py migrate           # Migrationen anwenden
python manage.py migrate --plan    # Plan anzeigen
```

### Entwicklung

```bash
python manage.py runserver         # Dev-Server starten
python manage.py createsuperuser   # Admin erstellen
python manage.py shell             # Django Shell
python manage.py collectstatic     # Static Files sammeln
```

### Tests

```bash
pytest                             # Alle Tests
pytest tests/test_erp.py           # Spezifische Tests
pytest --cov=apps/                 # Mit Coverage
```

### Code-Qualität

```bash
black apps/ tests/ config/         # Formatierung
flake8 apps/ tests/ config/        # Linting
mypy apps/                         # Type Checking
```

---

## Produktion

### Mit Gunicorn

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
pip install -r requirements-linux.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 0.0.0.0:8000 -w 4
```

### Mit Docker

```bash
docker-compose up -d
```

---

## Lizenzsystem

Das System unterstützt modulbasierte Lizenzen:

| Produkt | Features |
|---------|----------|
| ABORO_BASIC | Core, ERP Basis |
| ABORO_OFFICE | + CRM, HelpDesk |
| ABORO_PROFESSIONAL | + AI, Cloud-Storage |
| ABORO_ENTERPRISE | Alle Features |

Lizenzaktivierung über Django Admin: `/admin/licensing/`

---

## AI-Integration

### Anthropic Claude

```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Prompt"}]
)
```

### Ollama (Lokal)

```bash
# Installation: https://ollama.ai/download
ollama serve
ollama pull mistral
```

```python
from apps.helpdesk.services.ollama_service import OllamaService

ollama = OllamaService()
response = ollama.generate(prompt="Prompt", model="mistral")
```

---

## Troubleshooting

### ModuleNotFoundError: No module named 'django'

```bash
.venv\Scripts\activate           # Windows
source .venv/bin/activate        # Linux
pip install -r requirements-windows.txt
```

### pydantic-core build fails (Windows)

Verwende `requirements-windows.txt` (enthält pydantic 1.x ohne Rust-Kompilierung).

### psycopg2 Installation fehlgeschlagen

```bash
# Windows: Visual Studio Build Tools installieren
# Linux:
sudo apt-get install build-essential libpq-dev
```

### Connection refused (Ollama)

```bash
ollama serve   # In separatem Terminal
```

---

## Weitere Dokumentation

- `docs/API_INDEX.md` - API-Übersicht
- `docs/HELPDESK_API.md` - HelpDesk API
- `docs/CLOUDE_API.md` - Cloud-Storage API
- `docs/PLUGINS_DEVELOPER.md` - Plugin-Entwicklung
- `docs/USER_GUIDE.md` - Benutzerhandbuch

---

## Technologie-Stack

- **Backend:** Django 6.0.1, Django REST Framework
- **Datenbank:** SQLite (Dev), PostgreSQL (Prod)
- **Cache:** Redis
- **Task Queue:** Celery
- **WebSockets:** Django Channels
- **Frontend:** Bootstrap 5, HTMX
- **AI:** Anthropic Claude, Ollama

---

## Lizenz

Proprietär - ABoro GmbH

**Django Version:** 6.0.1  
**Python:** 3.9+
