# ABoroOffice ? Hilfe-Handbuch (voll)

## Inhaltsverzeichnis
1. CRM
2. ERP
3. Projekte
4. Workflows
5. Marketing
6. Vertraege
7. Personal
8. FiBu
9. Helpdesk
10. Cloud

## CRM
CRM Hilfe

 
 
 CRM Hilfe
 Leads, Accounts, Opportunities, KI, Enrich, API.
 

 
 Screens (ohne Bilder)
 
 
 Lead?Liste: /crm/leads/
 Lead?Detail: /crm/leads/&lt;id&gt;/
 Lead?Staging: /crm/staging/
 Accounts: /crm/accounts/
 Opportunities: /crm/opportunities/
 
 
 

 
 
 
 Schnellstart
 
 
 Lead anlegen (Name/Firma/Quelle).
 Website eintragen (Auto?Enrich).
 Notiz + Aktivit?t hinzuf?gen.
 Opportunity anlegen und Stage pflegen.
 Gewonnene Opportunity ? Angebot im ERP.
 
 
 
 
 
 
 Lead?Felder (Kurz)
 
 
 Name/Firma: Identifikation
 E?Mail/Telefon: Follow?up Kontakt
 Website: Auto?Enrich?Quelle
 Quelle: Pipeline?Analyse
 Status: z.?B. neu, qualifiziert, gewonnen
 
 
 
 
 

 
 
 
 Lead?Staging
 
 
 Profile steuern Keywords, Orte, Limit pro Run.
 Staging?Eintr?ge pr?fen, dann in Leads ?bernehmen.
 Fallback?Provider optional (Admin?Dashboard).
 
 
 
 
 
 
 Auto?Enrich
 
 Website vorhanden ? Telefon/Adresse/E?Mail werden extrahiert.
 Manuell ?ber ?Lead aus Website anreichern? im Lead?Detail.
 
 
 
 

 
 KI?Funktionen
 
 
 Zusammenfassung + n?chste Schritte
 Lead?Scoring (Regel + optional KI)
 Follow?up E?Mail Entwurf
 Q&A ?Frag die Kundenakte?
 
 
 

 
 Beispiel?Workflow
 
 
 Neuer Lead ? Status ?neu?.
 Auto?Enrich ? Kontakt vervollst?ndigen.
 Opportunity anlegen ? Stage ?proposal?.
 Stage ?won? ? ERP Angebot erzeugen.
 
 
 

 
 CRM API (Read/Write)
 
 Swagger
 /crm/api/docs/
 /crm/api/schema/
 
 Beispiel
 POST /crm/api/leads/
{"name":"Max Mustermann","company":"Example GmbH","email":"max@example.com","website":"https://example.de"}

## ERP
ERP Hilfe

 
 
 ERP Hilfe
 Angebot ? Auftrag ? Rechnung ? Mahnung.
 
 
 Pricing Hilfe
 
 

 
 Screens (ohne Bilder)
 
 
 Angebote: /erp/quotes/
 Auftr?ge: /erp/salesorders/
 Rechnungen: /erp/invoices/
 Mahnwesen: /erp/dunning/
 Wareneingang: /erp/stock/receipts/
 Kurse: /erp/courses/
 
 
 

 
 Workflow Angebot bis Rechnung
 
 
 Angebot erstellen (Angebotsnummer).
 Angebot annehmen ? Auftrag erzeugen.
 Auftragsbest?tigung wird erstellt.
 Auftrag ausf?hren ? Rechnung erzeugen.
 Mahnwesen bei Verzug.
 
 
 

 
 
 
 Nummern & Audit
 
 
 Eindeutige Nummern f?r Angebot/Auftrag/Rechnung/Mahnung.
 ?nderungen werden protokolliert.
 Suche in Angeboten/Auftr?gen/Rechnungen/Mahnungen.
 
 
 
 
 
 
 E?Mail & PDF
 
 
 PDF?Ausgabe mit Logo/Absender.
 E?Mail?Vorlagen im Admin?Dashboard.
 Scheduler f?r Rechnungs?/Mahnlauf.
 
 
 
 
 

 
 
 
 Wareneingang & Preise
 
 
 EK?Preis + MwSt ? Preisvorschlag.
 Konkurrenzpreis optional (Provider/Custom API).
 Rundung auf 0,05.
 
 
 
 
 
 
 Kurse & Personal
 
 
 Kurse mit Veranstaltungsnummer.
 Dozenten/Skills aus Personalverwaltung.
 Mobile Klassenr?ume als Produkt.
 
 
 
 
 

 
 Integrationen
 
 
 CRM ? Angebotserstellung
 FiBu ? Auto?Postings (Rechnung/Waren)
 Projekte ? automatisch aus Auftrag
 Workflows ? Trigger f?r Rechnung/Mahnung
 
 
 

 
 API
 
 Swagger
 /erp/api/docs/
 /erp/api/schema/
 
 Beispiel
 POST /erp/api/quotes/
{"customer":1,"valid_until":"2026-03-01"}

## Projekte
Projekte Hilfe

 
 Projektmanagement Hilfe
 Kanban, Gantt, WIP, Exporte und Integrationen.
 

 
 Screens (ohne Bilder)
 
 
 Projekt?bersicht: /projects/projects/
 Projekt?Detail: /projects/projects/&lt;id&gt;/
 Kanban: /projects/kanban/
 Gantt: /projects/gantt/
 Tasks: /projects/tasks/
 
 
 

 
 
 
 Schnellstart
 
 
 Projekt anlegen.
 Tasks + Meilensteine erstellen.
 Kanban f?r t?gliche Arbeit nutzen.
 Gantt f?r Planung/Reporting nutzen.
 
 
 
 
 
 
 Gantt vs. Kanban
 
 
 Kanban: Statusfluss (To Do ? In Progress ? Done).
 Gantt: Zeitachsen, Meilensteine, Verlauf.
 Empfehlung: Kanban operativ, Gantt strategisch.
 
 
 
 
 

 
 
 
 WIP?Limits
 
 
 Limit pro Spalte (To Do/In Progress/Blocked/Done).
 Limit pro Assignee und Team.
 Warnung + Modal?Details bei ?berschreitung.
 
 
 
 
 
 
 Exporte
 
 
 Gantt PDF/CSV: /projects/gantt/export/
 Zoom: Tag/Woche/Monat
 
 
 
 
 

 
 Integrationen
 
 
 ERP: Projekte entstehen automatisch aus Angeboten/Auftr?gen.
 CRM: Verlinkung ?ber Accounts/Opportunities.
 Workflows: Statuswechsel k?nnen Automationen triggern.
 
 
 

 
 Beispiel?Workflow
 
 
 ERP Angebot ? Auftrag.
 Projekt entsteht automatisch.
 Tasks ?ber Kanban abarbeiten.
 Meilensteine via Gantt reporten.

## Workflows
Workflows Hilfe

 
 Workflow?Automation Hilfe
 Trigger, Filter, Schritte, Beispiele.
 

 
 Screens (ohne Bilder)
 
 
 Workflows: /workflows/workflows/
 Workflow?Detail: /workflows/workflows/&lt;id&gt;/
 Workflow erstellen: /workflows/workflows/create/
 
 
 

 
 
 
 Schnellstart
 
 
 Workflow erstellen.
 Trigger?Typ w?hlen (CRM/ERP/Marketing).
 Filter (JSON) optional definieren.
 Schritte hinzuf?gen und aktivieren.
 
 
 
 
 
 
 Filter?Beispiele
 
 {"status":"won"}
 {"stage":["proposal","negotiation"]}
 {"status":"issued"}
 Die Filter werden gegen das jeweilige Objekt gepr?ft.
 
 
 
 

 
 
 
 Trigger?Typen
 
 
 CRM: Lead/Opportunity Status
 ERP: Auftrag/Rechnung/Mahnung
 Marketing: Content?Status
 
 
 
 
 
 
 Typische Schritte
 
 
 E?Mail senden
 Status ?ndern
 Task/Kommentar erstellen
 Webhook (optional)
 
 
 
 
 

 
 Beispiel?Workflows
 
 
 ERP: Rechnung erstellt ? E?Mail senden
 ERP: Mahnung erstellt ? E?Mail + Kommentar
 CRM: Opportunity gewonnen ? Projekt erstellen
 Marketing: Content freigegeben ? Task erstellen

## Marketing
Marketing Hilfe

 
 Marketing Hilfe
 Content?Workflow, Templates, Freigaben und KPIs.
 

 
 Screens (ohne Bilder)
 
 
 Marketing Home: /marketing/
 Assets: /marketing/assets/
 Kampagnen: /marketing/campaigns/
 Kalender: /marketing/calendar/
 
 
 

 
 
 
 Workflow
 
 
 Briefing erfassen
 AI?Entwurf erzeugen
 Freigabe anfordern
 Ver?ffentlichen
 
 
 
 
 
 
 Templates & Kan?le
 
 
 LinkedIn, Newsletter, Blog, Ads
 Regeln pro Kanal (Hashtags, Betreff, L?nge)
 Template anwenden im Asset?Workflow
 
 
 
 
 

 
 
 
 Freigaben & Rollen
 
 
 Approve?Gruppe darf freigeben
 View/Edit ?ber Gruppen steuerbar
 Versionierung bei Freigabe/Publish
 
 
 
 
 
 
 KPIs
 
 
 Impressions, Clicks, Conversions, Spend, Revenue
 CTR/CVR/ROI Berechnung
 CSV?Import + Trend?Ansicht
 
 
 
 
 

 
 Beispiel?Workflow
 
 
 Briefing erstellen ? AI?Entwurf.
 Freigabe durch Approver.
 Publish?Status setzt Content live.
 
 
 

 
 API
 
 Swagger
 /marketing/api/docs/
 /marketing/api/schema/
 
 Beispiel
 POST /marketing/api/assets/
{"title":"LinkedIn Post","channel":"LinkedIn","brief":"Kurz, CTA"}

## Vertraege
Vertr?ge Hilfe

 
 Vertragsverwaltung Hilfe
 Versionierung, Analyse, Freigabe und API.
 

 
 Screens (ohne Bilder)
 
 
 Vertragsliste: /contracts/
 Vertragsdetail: /contracts/&lt;id&gt;/
 Vertrag anlegen: /contracts/create/
 
 
 

 
 
 
 Schnellstart
 
 
 Vertrag anlegen (Titel, Gegenpartei).
 Dokument hochladen (PDF/DOCX).
 KI?Analyse starten (Zusammenfassung, Risiken).
 Versionen vergleichen/archivieren.
 
 
 
 
 
 
 KI?Analyse
 
 
 Zusammenfassung & Risiken
 Verpflichtungen/Deadlines
 Notizen als Basis f?r Verhandlungen
 
 
 
 
 

 
 
 
 Versionierung
 
 
 Neue Version bei ?nderungen
 Historie bleibt erhalten
 Audit?Sicherheit
 
 
 
 
 
 
 API
 
 Swagger
 /contracts/api/docs/
 /contracts/api/schema/

## Personal
Personal Hilfe

 
 Personalverwaltung Hilfe
 Mitarbeiter, Dozenten, Abteilungen und Zeiterfassung.
 

 
 Screens (ohne Bilder)
 
 
 Abteilungen: /personnel/departments/
 Mitarbeiter: /personnel/employees/
 Dozenten: /personnel/instructors/
 Skills: /personnel/skills/
 Zeiterfassung: /personnel/time-entries/
 
 
 

 
 
 
 Schnellstart
 
 
 Abteilung anlegen.
 Mitarbeiter/Dozenten anlegen.
 Skills zuweisen (f?r Kurse).
 Zeiterfassung pflegen und Export nutzen.
 
 
 
 
 
 
 ERP?Integration
 
 
 Dozenten sind mit Kursen verkn?pft.
 Skills steuern, welche Kurse m?glich sind.
 Zeiten unterst?tzen die Lohnabrechnung.
 
 
 
 
 

 
 
 
 Zeiterfassung
 
 
 Tages- und Monats?bersicht
 Einsatzort + Kostenstelle
 CSV?Export f?r Payroll
 
 
 
 
 
 
 API & Rechte
 
 Zugriff ?ber Gruppen/Staff steuerbar.
 API folgt dem globalen Auth?Modell (Login erforderlich).

## FiBu
FiBu Hilfe

 
 FiBu Hilfe
 Kontenplan, Kostenstellen, Buchungen und API.
 

 
 Screens (ohne Bilder)
 
 
 Journal: /fibu/journal/
 FiBu Settings: /fibu/settings/
 Kontenplan Import: /fibu/settings/
 
 
 

 
 
 
 Grundlagen
 
 
 Kontenplan (SKR04 Basis)
 Kostenarten & Kostenstellen
 Journalbuchungen mit Soll/Haben
 
 
 
 
 
 
 Auto?Postings
 
 
 ERP?Rechnungen ? Erl?se/USt/Debitor
 Wareneingang ? Lager/Verbindlichkeit
 Mapping im FiBu?Settings
 
 
 
 
 

 
 
 
 Import/Export
 
 
 Kontenplan via CSV importieren
 Journal-Export (CSV)
 
 
 
 
 
 
 API
 
 Swagger
 /fibu/api/docs/
 /fibu/api/schema/
 
 Beispiel
 POST /fibu/api/journal/
{"description":"Invoice 1001","lines":[{"account":8400,"debit":0,"credit":1190}]}

## Helpdesk
Helpdesk Hilfe

 
 Helpdesk Hilfe
 Tickets, Routing, Chat, Wissen, API?Referenz.
 

 
 Kern?Felder (Ticket)
 
 
 Titel: Kurzbeschreibung des Problems.
 Beschreibung: Details, Schritte, Kontext.
 Kunde: Bestandskunde oder neu.
 Kategorie: Routing + Reporting.
 Priorit?t: z.?B. niedrig/mittel/hoch.
 Status: neu/offen/in Arbeit/gel?st.
 Support?Level: L1?L4.
 Bereich/Queue: Teamzuordnung.
 
 
 

 
 Prozess: Routing?Regeln
 
 
 Ticket wird erstellt.
 Routing?Regeln pr?fen Kategorie/Keyword/Priorit?t.
 Passende Regel setzt Bereich/Queue/Support?Level.
 Benachrichtigungen gehen an Bereich/Queue?Gruppen.
 Fallback: L1/L2 wenn keine Regel greift.
 
 
 

 
 Prozess: Chat?Einbindung
 
 
 Widget?Code aus Helpdesk?Settings kopieren.
 Script im Frontend einbinden.
 Client startet Session ? Chat API.
 Agent ?bernimmt, antwortet, schlie?t Session.
 
 
 

 
 API?Referenz (genauer)
 
 
 
 Authentifizierung
 
 Ticket?API: Session?Login erforderlich (CSRF bei POST).
 Chat?Widget API: ?ffentlich (f?r Website?Widget).
 
 
 
 Pagination
 Kein Pagination?Default konfiguriert (REST_FRAMEWORK ohne Pagination). List?Endpoints liefern alle Eintr?ge.
 
Kunden?Suche
 GET /helpdesk/tickets/api/search-customers/?q=Max
 Parameter: q (String, erforderlich)
 200 OK
[{"id":1,"name":"Max Mustermann","email":"max@example.com"}]
Schema: [{id:int, name:string, email:string}]
 
 
 Ticket erstellen
 POST /helpdesk/tickets/api/create/
{"title":"Drucker defekt","priority":"high","category":2}
 Parameter: title (string), priority (string), optional category, customer
 201 Created
{"id":42,"status":"new"}
Schema: {id:int, title:string, status:string, priority:string, category:int|null, customer:int|null, support_level:string, department:int|null, queue:int|null, created_at:string, updated_at:string}
 
 
 Chat Session starten
 POST /helpdesk/chat/api/start/
{"name":"Max","email":"max@example.com"}
 Parameter: name, email
 200 OK
{"session_id":123}
Schema: {session_id:string, started_at:string, customer_name:string|null}
 
 
 Chat Nachricht senden
 POST /helpdesk/chat/api/send/
{"session_id":123,"message":"Hallo"}
 200 OK
{"ok":true}
Schema: {ok:boolean, message_id:int|null, queued:boolean|null}
 
 
 Fehlercodes (Standard)
 
 400 Ung?ltige Eingaben (fehlende Felder)
 403 Keine Berechtigung
 404 Objekt nicht gefunden
 500 Serverfehler
 
 
 
 

 
 Fehler?Diagnose (Beispiele)
 
 
 Chat Widget l?dt nicht ? Script?URL pr?fen, Mixed?Content vermeiden (HTTP/HTTPS).
 Ticket geht nicht an Queue ? Routing?Regeln + Kategorie pr?fen.
 Agent sieht Ticket nicht ? Gruppen/Queue?Berechtigung pr?fen.
 AI?Vorschl?ge leer ? Provider/Keys im Admin?Dashboard pr?fen.
 
 
 
 
 Fehler?Diagnose Checkliste
 
 
 Ticket fehlt ? Rolle/Gruppe + Queue pr?fen.
 Routing falsch ? Kategorie/Regel?Reihenfolge pr?fen.
 Chat Widget leer ? Script?URL + Mixed?Content pr?fen.
 API 403 ? Login/CSRF pr?fen.
 API 400 ? Pflichtfelder pr?fen.

## Cloud
Hilfe - CloudService

 
 
 
 
 Inhalt
 
 
 Dateiverwaltung
 Teilen
 Plugin?Lifecycle
 Berechtigungen
 Typische Fehler
 API?Referenz
 
 Entwickler?Doku
 
 
 
 

 
 Hilfe
 CloudService ? Dateien, Versionen und Freigaben.
 

 
 Dateiverwaltung
 
 
 Ordner erstellen, Dateien hochladen.
 Versionen werden automatisch gespeichert.
 Papierkorb f?r gel?schte Dateien.
 
 
 

 
 Teilen
 
 
 Freigaben an Benutzer/Gruppen.
 ?ffentliche Links (falls aktiviert).
 Passwort/Expiry f?r Links (optional).
 
 
 

 
 Plugin?Lifecycle
 
 
 Plugin installieren (ZIP/Repository).
 Aktivieren ? Widget erscheint.
 Optionen konfigurieren (falls vorhanden).
 Deaktivieren/Entfernen ? Widget verschwindet.
 
 
 

 
 Berechtigungen
 
 
 Freigaben an Benutzer oder Gruppen.
 Links k?nnen zeitlich begrenzt werden.
 Admins steuern Speicherquoten und globale Settings.
 
 
 

 
 Typische Fehler
 
 
 Upload fehlgeschlagen ? Dateigr??e/Typ pr?fen.
 Plugin nicht sichtbar ? Aktivierung + Position pr?fen.
 Freigabe ohne Zugriff ? Rechte/Gruppe pr?fen.
 
 
 

 
 
 Fehler?Diagnose Checkliste
 
 
 Upload scheitert ? Dateigr??e/Typ pr?fen.
 Share fehlt ? Rechte + Gruppe pr?fen.
 Plugin fehlt ? Aktivierung + Dashboard?Position pr?fen.
 API 403 ? Login/CSRF pr?fen.
 API 400 ? Pflichtfelder pr?fen.
 
 
 

 
 
 Fehler?Flow (Schritt?f?r?Schritt)
 
 
 Fehlercode notieren (400/403/404/500).
 Login/CSRF pr?fen (POST/DELETE).
 Pflichtfelder pr?fen (name, file, user).
 Rechte/Gruppe pr?fen.
 Plugin?Status + Dashboard?Position pr?fen.
 
 
 

 
 API?Referenz (genauer)
 
 
 
 Authentifizierung
 
 Cloud API: Session?Login erforderlich (CSRF bei POST).
 ?ffentliche Links (falls aktiviert) sind ohne Login erreichbar.
 
 
 
 Pagination
 Kein Pagination?Default konfiguriert. List?Endpoints liefern alle Eintr?ge.
 
Dateien
 GET /cloudstorage/api/files/?folder=1&search=report
 Parameter: folder (int, optional), search (string, optional)
 200 OK
[{"id":1,"name":"report.pdf","size":12345,"folder":1}]
Schema: [{id:int, name:string, size:int, folder:int|null, mime_type:string, created_at:string, updated_at:string}]
 
 
 Ordner erstellen
 POST /cloudstorage/api/folders/
{"name":"Projekte","parent":1}
 Parameter: name (string), parent (optional)
 201 Created
{"id":9,"name":"Projekte","parent":1}
Schema: {id:int, name:string, parent:int|null, created_at:string, updated_at:string}
 
 
 Freigabe erstellen
 POST /cloudstorage/api/shares/
{"file":1,"user":2,"permission":"read"}
 Parameter: file (int), user (int), permission (string)
 201 Created
{"id":55,"file":1,"user":2,"permission":"read"}
Schema: {id:int, file:int, user:int, permission:string, created_at:string, expires_at:string|null}
 
 
 Fehlercodes (Standard)
 
 400 Ung?ltige Eingaben
 403 Keine Berechtigung
 404 Objekt nicht gefunden
 500 Serverfehler
