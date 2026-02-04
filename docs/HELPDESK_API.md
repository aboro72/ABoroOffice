# Helpdesk API

**Base URL:** `/helpdesk/api/v1/`
**Auth:** Token via `/helpdesk/api/v1/auth/login/` (session auth works in browser).
**Swagger UI:** `/helpdesk/api/docs/`
**OpenAPI schema:** `/helpdesk/api/schema/`

## Auth & Headers
Most endpoints require:
- `Authorization: Token <token>`
- `X-License-Key: <license>`

You get the token via login, and the license key from your system admin.

## Auth
- `POST /helpdesk/api/v1/auth/login/` -> returns token
- `POST /helpdesk/api/v1/auth/logout/`
- `POST /helpdesk/api/v1/auth/validate-license/`

## Tickets
- `GET /helpdesk/api/v1/tickets/`
- `POST /helpdesk/api/v1/tickets/`
- `GET /helpdesk/api/v1/tickets/{id}/`
- `PATCH /helpdesk/api/v1/tickets/{id}/`
- `POST /helpdesk/api/v1/tickets/{id}/add_comment/`
- `POST /helpdesk/api/v1/tickets/{id}/assign/`
- `POST /helpdesk/api/v1/tickets/{id}/change_status/`

## Categories
- `GET /helpdesk/api/v1/categories/`

## Stats
- `GET /helpdesk/api/v1/stats/`
- `GET /helpdesk/api/v1/stats/performance/`
- `GET /helpdesk/api/v1/stats/by_agent/`

## Health
- `GET /helpdesk/api/v1/health/`

## Example: Login
```bash
curl -X POST -H "Content-Type: application/json"   -d '{"email":"agent@aboro.local","password":"Demo123!"}'   http://127.0.0.1:8000/helpdesk/api/v1/auth/login/
```

## Example: List Tickets
```bash
curl -H "Authorization: Token <token>"      -H "X-License-Key: <license>"      http://127.0.0.1:8000/helpdesk/api/v1/tickets/
```
