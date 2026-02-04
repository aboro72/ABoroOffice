# Phase 4/5 Integration: Migration & Test Prep

**Date:** 2026-02-04  
**Scope:** HelpDesk + CloudStorage (Cloude)

---

## 1) Migrations

```bash
# Create migrations for new apps (first time only)
python manage.py makemigrations helpdesk_api main cloude_api plugins

# Apply all migrations
python manage.py migrate
```

If you already have migrations, skip `makemigrations` and run `migrate` only.

---

## 2) System Checks

```bash
python manage.py check
```

---

## 3) Targeted Test Runs

```bash
# HelpDesk (tickets, knowledge, chat)
pytest apps/helpdesk -v

# Cloude (cloudstorage)
pytest apps/cloude -v
```

---

## 4) Optional: Smoke Run

```bash
python manage.py runserver
# HelpDesk: http://localhost:8000/helpdesk/
# CloudStorage: http://localhost:8000/cloudstorage/
# Cloud API Docs: http://localhost:8000/cloudstorage/api/docs/
```

---

## Notes
- HelpDesk auth lives at `/helpdesk/auth/` (Login/Logout/Register/Profile).
- CloudStorage auth lives at `/cloudstorage/accounts/`.
- Plugin storage directory is `plugins/installed/`.
