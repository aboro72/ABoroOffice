# ABoroOffice - Quick Start Guide

## Installation (Windows 11)

### 1. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Requirements
```bash
pip install -r requirements-windows.txt
```

### 3. Create Database
```bash
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000/admin/

---

## Installation (Linux)

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Requirements
```bash
pip install -r requirements-linux.txt
```

### 3-5. Same as Windows (steps 3-5 above)

---

## Project Structure

```
ABoroOffice/
├── apps/
│   ├── core/                 # Core models (ABoroUser, settings)
│   ├── licensing/            # License system & enforcement
│   └── classroom/            # Phase 2: Classroom management
│
├── config/
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # Dev-specific
│   │   └── production.py    # Prod-specific
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI config
│
├── templates/               # Django templates
├── tests/                   # Pytest test files
│
├── requirements.txt         # Reference file (read only)
├── requirements-windows.txt # Windows development
├── requirements-linux.txt   # Linux production
│
├── QUICKSTART.md           # This file
├── SETUP_REQUIREMENTS.md   # Platform-specific setup
├── AWS_BEDROCK_SETUP.md    # AWS Bedrock integration
└── OLLAMA_SETUP.md         # Ollama local models
```

---

## Key Features

### ✅ Phase 1: Foundation
- **User Management**: ABoroUser custom model
- **License System**: Feature-based access control
- **Admin Interface**: Django admin with customizations

### ✅ Phase 2: Classroom Management
- **Mobile Classrooms**: Inventory tracking
- **Deployments**: Schedule & track classroom deployments
- **Email Reminders**: Automatic notification scheduling
- **Checklists**: Inspection templates and completion tracking
- **Audit Trail**: Complete deployment history

### 🔜 Phase 3: Approvals (Planned)
- SSH approval workflow
- Excel/PDF report generation
- Email notifications

### 🔜 Phase 4: HelpDesk (Planned)
- Ticket management
- Knowledge base
- AI-powered responses
- Live chat support

### 🔜 Phase 5: Cloude (Planned)
- Cloud file storage
- Sharing & collaboration
- WebSocket real-time updates
- Plugin system

---

## AI Providers

### Anthropic Claude
```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Your prompt"}]
)
```

**Setup**: Already installed via `anthropic==0.30.1`

### AWS Bedrock
```python
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body=json.dumps({"messages": [...], "max_tokens": 1024})
)
```

**Setup**: See `AWS_BEDROCK_SETUP.md`

### Ollama (Local Models)
```python
from apps.helpdesk.services.ollama_service import OllamaService

ollama = OllamaService()
response = ollama.generate(
    prompt="Your prompt",
    model="mistral"
)
```

**Setup**:
1. Download: https://ollama.ai/download
2. Run: `ollama serve`
3. Pull model: `ollama pull mistral`
4. See `OLLAMA_SETUP.md` for details

---

## Common Commands

### Database
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration plan
python manage.py migrate --plan
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_classroom_models.py

# Run with coverage
pytest --cov=apps/ --cov-report=html
```

### Development
```bash
# Run server
python manage.py runserver

# Create admin user
python manage.py createsuperuser

# Shell with Django context
python manage.py shell

# Show installed apps
python manage.py showmigrations
```

### Utilities
```bash
# Collect static files
python manage.py collectstatic

# Format code
black apps/ tests/ config/

# Run linter
flake8 apps/ tests/ config/

# Type checking
mypy apps/
```

---

## Verification Checklist

After installation, verify everything works:

```bash
# 1. Check Python packages
python verify_requirements.py

# 2. Check Django
python manage.py check

# 3. Run migrations
python manage.py migrate

# 4. Run tests
pytest tests/

# 5. Start dev server
python manage.py runserver
# Visit http://localhost:8000/admin/
```

---

## Configuration Files

### Environment Variables (.env)
```bash
# Create .env file in project root
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# AWS Bedrock (if using)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Python Settings
- **Development**: `config/settings/development.py`
- **Production**: `config/settings/production.py`
- **Base (shared)**: `config/settings/base.py`

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'django'"
**Solution**: Install requirements and activate venv
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux
pip install -r requirements-windows.txt  # or requirements-linux.txt
```

### Issue: "No module named 'apps.classroom'"
**Solution**: Run migrations first
```bash
python manage.py migrate
```

### Issue: "psycopg2 build failed" (Windows)
**Solution**: Use psycopg2-binary (already in requirements)
```bash
pip install psycopg2-binary==2.9.11
```

### Issue: "Connection refused" (Ollama)
**Solution**: Start ollama service
```bash
ollama serve  # In another terminal
```

---

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/my-feature
```

### 2. Make Changes
```bash
# Edit code
# Run tests
pytest tests/

# Format code
black apps/
```

### 3. Commit Changes
```bash
git add .
git commit -m "Add my feature"
```

### 4. Run Full Test Suite
```bash
pytest --cov=apps/
```

### 5. Create Pull Request
```bash
git push origin feature/my-feature
gh pr create
```

---

## Performance Tips

1. **Use PostgreSQL** in production (not SQLite)
2. **Enable Redis caching** for sessions & ORM
3. **Use Celery** for long-running tasks
4. **Profile queries** with `django-debug-toolbar`
5. **Monitor with Sentry** (already configured)

---

## Useful Links

- [Django 6.0 Documentation](https://docs.djangoproject.com/en/6.0/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
- [AWS Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Ollama](https://ollama.ai)

---

## Next Steps

1. **Run migrations**: `python manage.py migrate`
2. **Create superuser**: `python manage.py createsuperuser`
3. **Start server**: `python manage.py runserver`
4. **Visit admin**: http://localhost:8000/admin/
5. **Explore classroom models**: Add test data in admin

---

**Status**: Phase 2 Complete, Phase 3 Ready to Start
**Django Version**: 6.0.1 (Latest)
**Python Support**: 3.9+
**Last Updated**: 2025-02-03
