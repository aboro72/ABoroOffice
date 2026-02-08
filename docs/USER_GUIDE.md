# ABoroOffice ? Benutzerhandbuch (Kurz)

## 1) ?berblick
ABoroOffice b?ndelt CRM, ERP, Vertr?ge, Marketing, Helpdesk, Projekte, Workflows, Personal und FiBu.

Startpunkte:
- Dashboard: `http://127.0.0.1:8000/dashboard/`
- Admin-Dashboard: `http://127.0.0.1:8000/admin-dashboard/`

Im Admin-Dashboard werden App-Toggles, Branding, E-Mail, Automationen, Rollen und zentrale Einstellungen verwaltet.

## 2) CRM
Zweck: Leads ? Opportunities ? Accounts.
- Lead-Staging: Einlesen + Anreicherung
- KI-Funktionen: Zusammenfassung, Next Steps, Follow-up Entwurf
- Verkn?pfung: ?bergabe in ERP (Angebot)

Hilfe: `/crm/help/`

## 3) ERP
Zweck: Angebote ? Auftr?ge ? Auftragsbest?tigung ? Rechnung ? Mahnung.
- Eindeutige Nummern f?r Angebot/Auftrag/Rechnung/Mahnung
- Automatischer Rechnungsversand und Mahnlauf (Scheduler)
- Verkn?pfung zu FiBu (Auto-Postings)
- Verkn?pfung zu Projekte (Projekt entsteht aus Auftrag)

Hilfe: `/erp/help/`
Pricing-Hilfe: `/erp/pricing-help/`

## 4) Projekte
Zweck: Aufgaben und Projektablauf.
- Kanban (Drag&Drop) + Swimlanes
- Gantt (mit Meilensteinen und Projekt-Zeitleiste)
- WIP-Limits pro Projekt + pro Assignee/Team

Hilfe: `/projects/help/`

## 5) Workflows (Automation)
Zweck: Automatisierte Aktionen ausl?sen.
Trigger:
- ERP: Rechnung ausgestellt, Mahnung erstellt, Auftrag Statuswechsel
- CRM: Lead-Statuswechsel, Opportunity-Stage
- Marketing: Content-Statuswechsel

Beispiele:
- Rechnung ? automatische Mail
- Mahnung ? automatische Mail
- Lead ?qualified? ? Task/Follow-up

Trigger-Filter (JSON) sind m?glich, z. B.:
- `{ "status": "won" }`
- `{ "stage": ["proposal", "negotiation"] }`

Hilfe: `/workflows/help/`

## 6) Vertr?ge
Zweck: Vertragsverwaltung + KI-Auswertung.
Hilfe: `/contracts/help/`

## 7) Marketing
Zweck: Content-Workflow (Briefing ? Entwurf ? Review ? Publish).
Hilfe: `/marketing/help/`

## 8) Personal
Zweck: Mitarbeiterverwaltung + Zeiterfassung + Payroll-Export.
Hilfe: `/personnel/help/`

## 9) FiBu
Zweck: Kontenplan, Kostenstellen, Buchungen.
Auto-Postings aus ERP (Rechnung/Waren).
Hilfe: `/fibu/help/`

## 10) Helpdesk
Zweck: Support-Tickets, Bereiche/Queues, Levels.
Hilfe: `/helpdesk/`

## 11) Cloud & Plugins
Cloud-Storage und Plugin-System.
Hilfe: `/cloudstorage/core/help/`

## 12) PDF Export
Das Benutzerhandbuch kann als PDF exportiert werden:
- `/user-guide/pdf/`
