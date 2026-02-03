# 🏢 ABoroOffice

Ein modulares, lizenziertes Enterprise-Management-System mit flexibler App-Aktivierung.

## 📦 Projektstruktur

```
ABoroOffice/
├── apps/                      # Modulare Anwendungen
│   ├── core/                  # Kern-Authentifizierung & Basis
│   ├── cloude/                # Cloude Service
│   └── helpdesk/              # HelpDesk Service
├── config/                    # Konfiguration
│   ├── licenses/              # Lizenzierungssystem
│   └── settings.py
├── docker/                    # Docker-Setup
├── docs/                      # Dokumentation
└── manage.py                  # Django Management
```

## 🔐 Lizenzierungssystem

Das System unterstützt:
- **Modul-basierte Lizenzen** - Einzelne Apps können lizensiert werden
- **Nachträgliche Aktivierung** - Apps können zur Laufzeit aktiviert werden
- **Flexible Verwaltung** - Einfache Admin-Oberfläche für Lizenzmanagement

## 🚀 Installation

1. Projekt klonen
2. `.env` Datei erstellen
3. `docker-compose up` ausführen

## 📝 Lizenz

Alle Dateien behalten ihre ursprüngliche Lizenzierung.
