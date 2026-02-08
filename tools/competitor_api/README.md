# Competitor Price API (Beispiel, FastAPI)

Ausfuehrlicher Beispiel‑Service fuer die ERP‑Konkurrenzpreis‑Schnittstelle.
Gedacht als Vorlage fuer eine eigene Preis‑Quelle (Partner, Marktplatz, internes Tool).

## 1) Installation (lokal)
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## 2) Start
```bash
set COMPETITOR_API_KEY=local-dev-key
.venv/Scripts/uvicorn app:app --host 0.0.0.0 --port 8010
```

## 3) ERP Konfiguration
Im Admin‑Dashboard:
- **ERP Konkurrenz‑Provider** = `Custom API`
- **API URL** = `http://127.0.0.1:8010/price`
- **API Key** = `local-dev-key`

## 4) Request
```
GET /price?q=Kynast%20Raeucherofen&sku=ABC-123
Authorization: Bearer local-dev-key
```

## 5) Response
```json
{
  "price_net": 129.9,
  "currency": "EUR",
  "source": "demo",
  "query": "Kynast Raeucherofen",
  "sku": "ABC-123"
}
```

## 6) Erwartete Felder
- `price_net` (float): Netto‑Preis (wird im ERP als Konkurrenzpreis genutzt)
- `currency` (string): z.B. `EUR`
- Optional: `source`, `query`, `sku` (nur zur Nachvollziehbarkeit)

## 7) Sicherheit
Wenn `COMPETITOR_API_KEY` gesetzt ist, wird `Authorization: Bearer <key>` erwartet.
Ohne Key nimmt der Service jede Anfrage an (nur fuer lokale Tests).
