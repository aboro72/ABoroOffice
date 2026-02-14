# API Documentation

## Übersicht

ABoroOffice bietet REST APIs für alle Module. Alle Endpoints erfordern Authentifizierung.

---

## ERP API

**Base URL:** `/erp/api/`

| Endpoint | Methoden | Beschreibung |
|----------|----------|--------------|
| `/customers/` | GET, POST | Kundenliste / Kunde erstellen |
| `/customers/{id}/` | GET, PUT, PATCH, DELETE | Kunde abrufen/bearbeiten/löschen |
| `/products/` | GET, POST | Produktliste |
| `/products/{id}/` | GET, PUT, PATCH, DELETE | Produkt bearbeiten |
| `/categories/` | GET, POST | Produktkategorien |
| `/categories/{id}/` | GET, PUT, PATCH, DELETE | Kategorie bearbeiten |
| `/services/` | GET, POST | Dienstleistungen |
| `/services/{id}/` | GET, PUT, PATCH, DELETE | Dienstleistung bearbeiten |
| `/workorders/` | GET, POST | Arbeitsaufträge |
| `/workorders/{id}/` | GET, PUT, PATCH, DELETE | Arbeitsauftrag bearbeiten |
| `/quotes/` | GET, POST | Angebote |
| `/quotes/{id}/` | GET, PUT, PATCH, DELETE | Angebot bearbeiten |
| `/quote-items/` | GET, POST | Angebotspositionen |
| `/salesorders/` | GET, POST | Aufträge |
| `/salesorders/{id}/` | GET, PUT, PATCH, DELETE | Auftrag bearbeiten |
| `/salesorder-items/` | GET, POST | Auftragspositionen |
| `/order-confirmations/` | GET, POST | Auftragsbestätigungen |
| `/invoices/` | GET, POST | Rechnungen |
| `/invoices/{id}/` | GET, PUT, PATCH, DELETE | Rechnung bearbeiten |
| `/dunning-notices/` | GET, POST | Mahnungen |
| `/dunning-notices/{id}/` | GET, PUT, PATCH, DELETE | Mahnung bearbeiten |
| `/stock-receipts/` | GET, POST | Wareneingänge |
| `/stock-receipt-items/` | GET, POST | Wareneingangs-Positionen |
| `/courses/` | GET, POST | Veranstaltungen |
| `/courses/{id}/` | GET, PUT, PATCH, DELETE | Veranstaltung bearbeiten |
| `/enrollments/` | GET, POST | Anmeldungen |

**Swagger UI:** `/erp/api/docs/`

---

## Personnel API

**Base URL:** `/personnel/api/`

| Endpoint | Methoden | Beschreibung |
|----------|----------|--------------|
| `/external-employees/` | GET, POST | Externe Mitarbeiter |
| `/external-employees/{id}/` | GET, PUT, PATCH, DELETE | Externer MA bearbeiten |
| `/employees/` | GET, POST | Mitarbeiter |
| `/employees/{id}/` | GET, PUT, PATCH, DELETE | Mitarbeiter bearbeiten |
| `/departments/` | GET, POST | Abteilungen |
| `/departments/{id}/` | GET, PUT, PATCH, DELETE | Abteilung bearbeiten |
| `/skills/` | GET, POST | Skills/Kompetenzen |
| `/skills/{id}/` | GET, PUT, PATCH, DELETE | Skill bearbeiten |
| `/time-entries/` | GET, POST | Zeiterfassung |
| `/time-entries/{id}/` | GET, PUT, PATCH, DELETE | Zeiteintrag bearbeiten |

### Filter-Parameter (Personnel)

**Employees:**
- `?department=<id>` - Nach Abteilung filtern
- `?is_active=true/false` - Nach Status filtern
- `?employment_type=full_time|part_time|contract|temp`

**Time Entries:**
- `?employee=<id>` - Nach Mitarbeiter
- `?department=<id>` - Nach Abteilung
- `?month=YYYY-MM` - Nach Monat
- `?date_from=YYYY-MM-DD` - Von Datum
- `?date_to=YYYY-MM-DD` - Bis Datum

---

## CRM API

**Base URL:** `/crm/api/`

| Endpoint | Methoden | Beschreibung |
|----------|----------|--------------|
| `/accounts/` | GET, POST | Accounts/Firmen |
| `/accounts/{id}/` | GET, PUT, PATCH, DELETE | Account bearbeiten |
| `/leads/` | GET, POST | Leads |
| `/leads/{id}/` | GET, PUT, PATCH, DELETE | Lead bearbeiten |
| `/opportunities/` | GET, POST | Opportunities |
| `/opportunities/{id}/` | GET, PUT, PATCH, DELETE | Opportunity bearbeiten |
| `/activities/` | GET, POST | Aktivitäten |
| `/activities/{id}/` | GET, PUT, PATCH, DELETE | Aktivität bearbeiten |
| `/notes/` | GET, POST | Notizen |
| `/notes/{id}/` | GET, PUT, PATCH, DELETE | Notiz bearbeiten |

---

## HelpDesk API

**Base URL:** `/helpdesk/api/`

Siehe `docs/HELPDESK_API.md` für vollständige Dokumentation.

| Endpoint | Beschreibung |
|----------|--------------|
| `/tickets/` | Ticket-Management |
| `/chat/` | Chat-Nachrichten |
| `/knowledge/` | Knowledge Base |

**Swagger UI:** `/helpdesk/api/docs/`

---

## Cloud Storage API

**Base URL:** `/cloudstorage/api/`

Siehe `docs/CLOUDE_API.md` für vollständige Dokumentation.

| Endpoint | Beschreibung |
|----------|--------------|
| `/files/` | Datei-Management |
| `/folders/` | Ordner-Management |
| `/shares/` | Freigaben |

**Swagger UI:** `/cloudstorage/api/docs/`

---

## Authentifizierung

Alle API-Anfragen erfordern einen gültigen Session-Cookie oder Token.

### Session-Auth (Browser)
```bash
# Login über Web-Interface
# Cookie wird automatisch gesetzt
```

### Token-Auth (Programmatisch)
```bash
curl -X POST /api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Response: {"token": "abc123..."}

# Verwenden:
curl -H "Authorization: Token abc123..." /erp/api/customers/
```

---

## Allgemeine Parameter

Alle List-Endpoints unterstützen:

| Parameter | Beschreibung |
|-----------|--------------|
| `?search=<text>` | Volltextsuche |
| `?ordering=<field>` | Sortierung (- für absteigend) |
| `?page=<n>` | Pagination |
| `?page_size=<n>` | Einträge pro Seite |

### Beispiele

```bash
# Suche nach Kunden
GET /erp/api/customers/?search=Müller

# Sortiert nach Erstelldatum (neueste zuerst)
GET /erp/api/invoices/?ordering=-created_at

# Produkte mit niedrigem Lagerbestand
GET /erp/api/products/?ordering=stock_qty

# Zeiteinträge für einen Monat
GET /personnel/api/time-entries/?month=2026-02
```

---

## Response-Format

Alle Responses sind JSON:

```json
{
  "count": 42,
  "next": "/erp/api/customers/?page=2",
  "previous": null,
  "results": [
    {"id": 1, "name": "Kunde A", ...},
    {"id": 2, "name": "Kunde B", ...}
  ]
}
```

Einzelne Objekte:
```json
{
  "id": 1,
  "name": "Kunde A",
  "email": "kunde@example.com",
  "created_at": "2026-02-14T10:30:00Z"
}
```

---

## Fehler-Codes

| Code | Bedeutung |
|------|-----------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (Delete) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

---

## Weitere Dokumentation

- `docs/HELPDESK_API.md` - HelpDesk API Details
- `docs/CLOUDE_API.md` - Cloud Storage API Details
- `docs/PLUGINS_DEVELOPER.md` - Plugin-Entwicklung
