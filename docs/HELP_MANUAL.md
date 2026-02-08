# ABoroOffice ? Hilfe?Handbuch (voll)

## 0) Index
1. ?berblick
2. CRM
3. ERP
4. Projekte
5. Workflows
6. Marketing
7. Vertr?ge
8. Personal
9. FiBu
10. Helpdesk
11. Cloud/Plugins
12. Fehler & Diagnose
13. API?Referenz (Kurz)

## 1) ?berblick
Dieses Handbuch fasst alle Hilfe?Seiten zusammen und erkl?rt Prozesse, Felder, Fehlerbilder und APIs.

## 2) CRM
**Kernfelder**: Name, Firma, E?Mail, Telefon, Website, Quelle, Status.  
**Workflow**: Lead ? Opportunity ? Angebot (ERP).  
**KI**: Summary, Next Steps, Follow?up.

## 3) ERP
**Workflow**: Angebot ? Auftrag ? Best?tigung ? Rechnung ? Mahnung.  
**Nummern**: eindeutige Nummern f?r alle Belege.  
**Wareneingang**: EK + MwSt ? Preisvorschlag; Konkurrenzpreis optional.

## 4) Projekte
**Kanban** f?r operative Steuerung, **Gantt** f?r Planung/Reporting.  
**WIP?Limits**: pro Spalte, Assignee, Team.

## 5) Workflows
**Trigger**: CRM/ERP/Marketing Statuswechsel.  
**Filter**: JSON?basiert.  
**Schritte**: E?Mail, Status, Task, Kommentar.

## 6) Marketing
**Workflow**: Briefing ? AI Entwurf ? Freigabe ? Publish.  
**KPIs**: Impressions, Clicks, Conversions, ROI.

## 7) Vertr?ge
**Upload**: PDF/DOCX, Versionierung, KI?Analyse.

## 8) Personal
**Abteilungen, Mitarbeiter, Dozenten, Skills.**  
**Zeiterfassung** mit Export.

## 9) FiBu
**Kontenplan** (SKR04), **Kostenstellen**, **Journal**.  
**Auto?Postings** aus ERP.

## 10) Helpdesk
**Routing**: Regeln setzen Bereich/Queue/Level.  
**Chat**: Widget ? Session ? Agent.  
**API**: Tickets/Chat mit Session?Auth (Ticket) und public (Chat Widget).

## 11) Cloud/Plugins
**Versionierung**, **Shares**, **Papierkorb**.  
**Plugin?Lifecycle**: installieren ? aktivieren ? konfigurieren ? entfernen.

## 12) Fehler & Diagnose (Checkliste)
1. API 403 ? Login/CSRF pr?fen.
2. API 400 ? Pflichtfelder pr?fen.
3. Chat Widget leer ? Script?URL/Mixed?Content.
4. Plugin fehlt ? Aktivierung/Position.
5. Routing falsch ? Regeln pr?fen.

## 13) API?Referenz (Kurz)
- CRM: `/crm/api/docs/`
- ERP: `/erp/api/docs/`
- Marketing: `/marketing/api/docs/`
- Vertr?ge: `/contracts/api/docs/`
- FiBu: `/fibu/api/docs/`
- Cloud: `/cloudstorage/api/...`
- Helpdesk: `/helpdesk/tickets/api/...` + `/helpdesk/chat/api/...`
