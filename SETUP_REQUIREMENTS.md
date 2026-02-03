# ABoroOffice - Requirements Setup Guide

## Platform-Specific Requirements

ABoroOffice now uses **platform-specific requirement files** to handle OS-level dependency differences, particularly around packages that require native compilation.

### Why Two Files?

**Windows 11 vs Linux** have different capabilities:
- **Windows**: No Rust compiler by default, requires pre-built wheels
- **Linux**: Can compile from source, optimized for production

The key difference is **pydantic**:
- **Windows**: pydantic 1.10.13 (pre-built wheels, no compilation needed)
- **Linux**: pydantic 2.5.3 (full version, requires Rust toolchain)

## Installation Instructions

### For Windows 11 Development

```bash
# Install Windows-specific requirements
pip install -r requirements-windows.txt

# Verify installation
python -m pip check
pytest tests/ -v
```

**Includes:**
- ✅ All development tools (pytest, black, flake8, etc.)
- ✅ pydantic 1.10.13 (backward compatible, no Rust needed)
- ✅ Windows-compatible packages only
- ✅ PostgreSQL support via psycopg2-binary
- ❌ uwsgi (Linux-only, use gunicorn instead)

### For Linux Production/Deployment

```bash
# Install Linux-specific requirements
pip install -r requirements-linux.txt

# Verify installation
python -m pip check
pytest tests/ -v
```

**Includes:**
- ✅ All production packages
- ✅ pydantic 2.5.3 (latest stable, with Rust compilation)
- ✅ uwsgi (production WSGI server for Linux/Unix)
- ✅ PostgreSQL support via psycopg2-binary
- ✅ All optional packages enabled

## Version Notes

### Django 6.0.1 (Latest)
- Latest stable release with all modern features
- Compatible with all integrated apps (HelpDesk, Classroom, Cloude, Approvals)
- Updated all dependencies for Django 6.0 compatibility

### Pydantic Version Difference

| Aspect | Windows (1.10.13) | Linux (2.5.3) |
|--------|-------------------|---------------|
| Compilation | Pre-built wheels | Rust + maturin |
| Performance | Good | Better |
| Backward compat | High | Requires v2 style |
| Installation speed | Fast | ~2-5 min (Rust) |
| Dependencies | django-ckeditor, anthropic, ollama | Same + pre-built |

### Key Dependencies

**Core Stack (Both):**
- Django==6.0.1 (Latest stable)
- djangorestframework==3.14.0 (Django 6.0 compatible)
- channels==4.3.2 (WebSockets support)
- celery==5.6.2 (Task queue)
- redis==7.1.0 (Caching)

**Feature Modules:**
- HelpDesk: django-ckeditor, anthropic, ollama
- Classroom: paramiko (SSH), pandas, openpyxl
- Cloude: django-guardian, django-jazzmin
- Approvals: paramiko, openpyxl, python-docx

## Troubleshooting

### Issue: `pydantic-core` build fails on Windows

**Cause:** Trying to build pydantic 2.5.3 from source requires Rust compiler.

**Solution:** Use `requirements-windows.txt` which includes pydantic 1.10.13 (pre-built wheels).

```bash
# Remove any cached wheels
pip cache purge

# Install fresh with Windows requirements
pip install -r requirements-windows.txt
```

### Issue: `psycopg2-binary` installation fails

**Cause:** Missing build tools or PostgreSQL dev libraries.

**Windows Solution:**
```bash
# Ensure VC++ build tools are installed
# Visual Studio Build Tools (free): https://visualstudio.microsoft.com/downloads/
# Then retry: pip install psycopg2-binary
```

**Linux Solution:**
```bash
# Debian/Ubuntu
sudo apt-get install build-essential postgresql-client libpq-dev

# Fedora/CentOS
sudo dnf install postgresql-devel
```

### Issue: `paramiko` installation fails on Windows

**Cause:** Missing cryptography dependencies.

**Solution:**
```bash
pip install --upgrade cryptography==41.0.7
pip install paramiko==4.0.0
```

### Issue: Tests fail on Windows but work on Linux

**Possible Causes:**
- Path separators (use `pathlib.Path` not hard-coded `/`)
- Line endings (ensure `.gitattributes` normalizes)
- Timezone handling (use UTC in tests)

**Solution:**
```bash
# Verify no OS-specific code in tests
pytest tests/ -v --tb=short
```

## Verification Checklist

After installation, verify everything works:

```bash
# 1. Check dependencies are installed correctly
python -m pip check

# 2. Verify Django installation
python manage.py --version

# 3. Run migrations (requires database setup first)
python manage.py migrate --plan

# 4. Run tests
pytest tests/ -v --cov=apps/

# 5. Check admin interface loads
python manage.py runserver
# Visit http://localhost:8000/admin/
```

## Development Workflow

### Windows 11 Developer Machine

```bash
# Initial setup
git clone <repo>
cd ABoroOffice
python -m venv venv
venv\Scripts\activate  # Windows activation script
pip install -r requirements-windows.txt
python manage.py migrate
python manage.py runserver
```

### Linux Production Server

```bash
# Initial setup
git clone <repo>
cd ABoroOffice
python -m venv venv
source venv/bin/activate  # Linux activation script
pip install -r requirements-linux.txt
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 -w 4
```

## Reference: requirements.txt

The main `requirements.txt` file serves as a **reference only** and contains all dependencies with comments. It's not meant for direct installation due to platform conflicts. Always use:
- `requirements-windows.txt` for Windows development
- `requirements-linux.txt` for Linux production

## Future: Python Version Compatibility

- **reportlab**: Requires Python <3.9 (legacy package)
  - Planned for Phase 4+ with separate Python environment or compatible fork
  - Will be added to separate `requirements-legacy.txt` when needed

## Updating Requirements

To update dependencies while maintaining platform separation:

1. Update all three files with any new/changed package versions
2. Test on Windows: `pip install -r requirements-windows.txt && pytest`
3. Test on Linux: `pip install -r requirements-linux.txt && pytest`
4. Document changes in CHANGELOG.md

---

**Last Updated:** 2025-02-03
**Django Version:** 6.0.1 (Latest)
**Status:** Platform-specific requirements configured and tested with Django 6.0.1
