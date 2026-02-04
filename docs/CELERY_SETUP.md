# Celery Setup für Phase 3 (Approvals)

**Status**: ✅ Konfiguriert für Priority 2 (Celery Tasks)

---

## Overview

Celery ist jetzt vollständig konfiguriert für async Email und SSH Execution Tasks.

### Komponenten
- ✅ `config/celery.py` - Celery App Konfiguration
- ✅ `apps/approvals/celery_tasks.py` - Alle Task Definitionen
- ✅ `apps/approvals/signals.py` - Auto-triggering von Tasks
- ✅ `config/settings/base.py` - Celery + Beat Schedule

---

## Abhängigkeiten

Diese sollten bereits in requirements installiert sein:
```
celery==5.6.2
redis==7.1.0  (für Broker)
paramiko==4.0.0  (für SSH)
```

Falls nicht:
```bash
pip install celery==5.6.2 redis==7.1.0 paramiko==4.0.0
```

---

## Redis Setup (Required)

Celery braucht Redis als Message Broker.

### Windows (via WSL oder Docker)
```bash
# Option 1: Docker
docker run -d -p 6379:6379 redis:latest

# Option 2: WSL
wsl redis-server
```

### macOS
```bash
brew install redis
redis-server
```

### Linux
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

---

## Development: Celery Worker starten

### Terminal 1: Django Dev Server
```bash
python manage.py runserver
```

### Terminal 2: Celery Worker (foreground)
```bash
celery -A config worker -l info
```

Für Debugging mit mehr Logging:
```bash
celery -A config worker -l debug -c 1 --without-gossip --without-mingle
```

### Terminal 3: Celery Beat (Scheduler, optional)
```bash
celery -A config beat -l info
```

Kombiniert (nicht empfohlen für Produktion):
```bash
celery -A config worker --beat -l info
```

---

## Celery Tasks Übersicht

### Email Tasks

#### `send_approval_email_task(approval_id)`
- **Trigger**: Signal nach Approval erstellt
- **Action**: Sendet Approval Request Email
- **Retry**: 3x mit 60s Delay
- **Status**: ✅ Ready

#### `send_reminder_email_task(approval_id, reminder_number)`
- **Parameter**: reminder_number ∈ {1, 2, 3}
- **Trigger**: Manuell oder Scheduler
- **Retry**: 3x mit 60s Delay
- **Status**: ✅ Ready

#### `send_approval_confirmed_email_task(approval_id)`
- **Trigger**: Signal nach Approval approved
- **Action**: Sendet Bestätigungs-Email
- **Status**: ✅ Ready

#### `send_approval_rejected_email_task(approval_id)`
- **Trigger**: Signal nach Approval rejected
- **Action**: Sendet Ablehnung-Email
- **Status**: ✅ Ready

### SSH Task

#### `execute_ssh_approval_task(approval_id)`
- **Trigger**: Signal nach Approval approved
- **Action**: SSH-Befehl auf Server ausführen
- **Retry**: 2x mit 300s Delay
- **Status**: ✅ Ready (benötigt SSH Credentials Config)
- **Note**: Benötigt Umgebungsvariablen für SSH Credentials

### Scheduler Tasks (Celery Beat)

#### `check_approval_deadlines()`
- **Schedule**: Stündlich (jede volle Stunde)
- **Action**: Markiere abgelaufene Approvals als 'expired'
- **Status**: ✅ Ready

#### `check_server_health()`
- **Schedule**: Alle 15 Minuten
- **Action**: Checke SSH Erreichbarkeit der Server
- **Status**: ✅ Ready

---

## Testing in Development

### Test 1: Task ausführen im Shell
```python
python manage.py shell

# Import Tasks
from apps.approvals.celery_tasks import send_approval_email_task
from apps.approvals.models import Approval

# Get an approval
approval = Approval.objects.first()

# Trigger task (if Celery Worker running)
send_approval_email_task.delay(approval.id)

# Or execute synchronously (for testing)
result = send_approval_email_task(approval.id)
print(result)
```

### Test 2: Approval erstellen (auto trigger email)
```python
from apps.approvals.models import Approval, RatingSchedule
from django.utils import timezone
from datetime import timedelta

schedule = RatingSchedule.objects.first()

approval = Approval.objects.create(
    server_name='test-server',
    server_port=1425,
    rating_schedule=schedule,
    email_recipients=['test@example.com'],
    scheduled_time=timezone.now() + timedelta(hours=1),
    deadline=timezone.now() + timedelta(days=1),
    status='pending'
)

# Signal sollte automatisch Email Task queuen
# Checke: [INFO] Queued approval email for {approval.token}
```

### Test 3: Approval genehmigen (auto trigger ssh + confirmation email)
```python
approval = Approval.objects.first()
approval.status = 'approved'
approval.approved_by = 'test@example.com'
approval.approved_at = timezone.now()
approval.approval_method = 'api'
approval.save()

# Signal sollte automatisch folgendes queuen:
# - SSH execution task
# - Approval confirmed email task
```

---

## Email Configuration

### Für Development (Console Backend)
Emails werden zu Console ausgegeben (default):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Für Production (SMTP)
Setze Umgebungsvariablen:
```bash
export EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
export EMAIL_HOST='smtp.gmail.com'
export EMAIL_PORT='587'
export EMAIL_USE_TLS='True'
export EMAIL_HOST_USER='your-email@gmail.com'
export EMAIL_HOST_PASSWORD='your-app-password'
export DEFAULT_FROM_EMAIL='approvals@aboro.office'
```

---

## SSH Configuration

### Sicherheitswarnung ⚠️

**Current Implementation**: SSH Credentials sind hardcoded als Placeholder!

```python
ssh_client.connect(
    approval.server_name,
    port=approval.server_port,
    username='approval_user',  # ⚠️ Placeholder!
    timeout=ssh_timeout
)
```

### Zu Implementieren (TODO)

1. **SSH Credentials Storage**:
   - Umgebungsvariablen
   - Environment Vault
   - SSH Key-based Auth (empfohlen)

2. **SSH Key Setup**:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/aboro_approval_key
# Add public key to target servers
ssh-copy-id -i ~/.ssh/aboro_approval_key user@server
```

3. **Code Update**:
```python
ssh_client.connect(
    hostname=approval.server_name,
    port=approval.server_port,
    username=os.getenv('SSH_USER', 'approval_user'),
    key_filename=os.getenv('SSH_KEY_PATH'),  # Key-based auth
    timeout=ssh_timeout
)
```

---

## Logging

### Celery Worker Logs
```
[2025-02-04 10:30:00,123: INFO/MainProcess] Received task: apps.approvals.celery_tasks.send_approval_email_task
[2025-02-04 10:30:00,456: INFO/PoolWorker-1] Sending approval email for approval 1
[2025-02-04 10:30:01,789: INFO/PoolWorker-1] Task apps.approvals.celery_tasks.send_approval_email_task succeeded
```

### Django Logs
```
[INFO] apps.approvals.signals: New approval created: a1b2c3d4-...
[INFO] apps.approvals.signals: Queued approval email for a1b2c3d4-...
[DEBUG] apps.approvals.email_service: Approval request email sent for a1b2c3d4-... to ['test@example.com']
```

### Location
- **File**: `logs/aboro.log` (rotating, 10MB max)
- **Console**: Terminal output (development)

---

## Fehlerbehebung

### Problem: "Connection refused" (Celery)
```
Error: Couldn't connect to Redis at localhost:6379
```
**Lösung**: Redis nicht läuft
```bash
# Start Redis
redis-server
```

### Problem: "No module named celery"
```
Error: ModuleNotFoundError: No module named 'celery'
```
**Lösung**: Celery nicht installiert
```bash
pip install celery==5.6.2
```

### Problem: Tasks werden nicht ausgeführt
```
Task ist gequeued aber Celery Worker führt sie nicht aus
```
**Lösung**: Worker ist nicht läuft
```bash
celery -A config worker -l info
```

### Problem: Imports fehlgeschlagen
```
Error: ImportError in app startup
```
**Lösung**: app.py hat signal import falsch
```python
# config/settings/base.py in apps.py ready()
def ready(self):
    import apps.approvals.signals  # ← Should be this
```

---

## Monitoring (Optional)

### Celery Flower (Web UI für Tasks)
```bash
pip install flower
celery -A config events --broker=redis://localhost:6379
# In another terminal:
celery -A config purge  # Clear queue
flower -A config --port=5555
# Visit http://localhost:5555
```

---

## Production Deployment

### Best Practices
1. ✅ Use Redis (hosted or managed)
2. ✅ Use Supervisor or systemd for workers
3. ✅ Separate Celery Beat scheduler
4. ✅ Monitor with Flower or Prometheus
5. ✅ Configure proper logging
6. ✅ Use SSH key-based auth (not passwords)

### Example Systemd Service
```ini
[Unit]
Description=ABoroOffice Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=www-data
WorkingDirectory=/path/to/ABoroOffice
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/path/to/venv/bin/celery -A config worker --loglevel=info --logfile=-

[Install]
WantedBy=multi-user.target
```

---

## Next Steps (Priority 3)

### Views & API Endpoints
- [ ] ApprovalListView
- [ ] ApprovalDetailView
- [ ] ApprovalApproveView (email token)
- [ ] ApprovalRejectView
- [ ] API endpoints (DRF)

**Estimated**: 2.5 hours

---

**Last Updated**: 2025-02-04
**Status**: Phase 3 Priority 2 Complete ✅
