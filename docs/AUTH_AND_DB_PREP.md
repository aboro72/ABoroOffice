# Auth and Database Preparation

This document describes preparation steps for supporting multiple databases and future authentication options.
These changes are intentionally non-invasive and do not enable new auth flows yet.

## Multi-DB (SQLite, MariaDB/MySQL, MSSQL, PostgreSQL)

### Current behavior
- Default uses SQLite in `db.sqlite3`.
- You can switch by setting `DB_ENGINE` in `.env`.

### Supported DB_ENGINE values
- `sqlite`
- `postgres` / `postgresql`
- `mysql` / `mariadb`
- `mssql`

### Notes per engine
- MariaDB/MySQL:
  - Engine: `django.db.backends.mysql`
  - Recommended charset: `utf8mb4`
  - Install: `mysqlclient` (or `PyMySQL`, if preferred)
- MSSQL:
  - Engine: `mssql` (via `mssql-django`)
  - Driver example: `ODBC Driver 18 for SQL Server`
  - Install: `mssql-django` and SQL Server ODBC driver
- MongoDB:
  - Not wired into Django ORM yet.
  - Use only for future non-ORM use cases (logs, analytics, etc.).

### Optional dependency set (not enabled yet)
Add when you decide to use each DB:
- MariaDB/MySQL: `mysqlclient` (or `PyMySQL`)
- MSSQL: `mssql-django`
- PostgreSQL: `psycopg2-binary`

### Migration strategy (SQLite -> MariaDB/MSSQL)
High-level approach:
1. Create target DB and credentials.
2. Configure `.env` with `DB_ENGINE`, `DB_HOST`, `DB_NAME`, etc.
3. Install DB driver dependency.
4. Run `python manage.py migrate` on the new DB.
5. Export data from SQLite and import to target DB:
   - Option A: Use `dumpdata`/`loaddata` for smaller datasets.
   - Option B: Use a dedicated migration tool for larger datasets.
6. Validate: counts and key business tables.

### Example `.env` (MariaDB)
```
DB_ENGINE=mariadb
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aboro_db
DB_USER=aboro_user
DB_PASSWORD=change_me
```

### Example `.env` (MSSQL)
```
DB_ENGINE=mssql
DB_HOST=localhost
DB_PORT=1433
DB_NAME=aboro_office
DB_USER=aboro
DB_PASSWORD=change_me
MSSQL_DRIVER=ODBC Driver 18 for SQL Server
```

## Auth Preparation (Email Login, Microsoft, Google)

### Email-as-login (future)
Potential approach:
- Switch `ABoroUser.USERNAME_FIELD` to `email`.
- Add a custom authentication backend to allow login with email.
- Migrate data and enforce unique email addresses.

This is not enabled yet. Current login still uses username.

### Microsoft / Google OAuth (future)
Recommended approach:
- Use `django-allauth` with OAuth providers.
- Add client IDs/secrets via environment variables.
- Expose a chooser UI on the login page.

### Proposed rollout steps (no activation yet)
1. Add an `AUTH_ALLOW_EMAIL_LOGIN` flag (already in `.env.example`).
2. Create a dedicated authentication backend that:
   - Accepts email or username.
   - Normalizes email and checks `email_verified` when required.
3. Ensure `ABoroUser.email` is unique and indexed.
4. Add a migration to backfill missing emails or enforce constraints.
5. Add provider config for `django-allauth`:
   - Microsoft: `openid_connect` with tenant support.
   - Google: standard OAuth.
6. Add optional login buttons (only visible when client IDs are set).

Environment placeholders are present in `.env.example`:
- `OAUTH_MICROSOFT_CLIENT_ID`
- `OAUTH_MICROSOFT_CLIENT_SECRET`
- `OAUTH_MICROSOFT_TENANT_ID`
- `OAUTH_GOOGLE_CLIENT_ID`
- `OAUTH_GOOGLE_CLIENT_SECRET`
