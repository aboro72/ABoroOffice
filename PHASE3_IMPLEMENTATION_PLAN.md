# Phase 3: SSH Approval Workflow Implementation

**Status**: Starting
**Estimated Duration**: 1-2 weeks
**Source**: `C:\Users\aborowczak\PycharmProjects\dokmbw_web_app\approvals\`
**Target**: `apps/approvals/` in ABoroOffice

---

## Overview

Phase 3 integrates the SSH Approval Workflow from dokmbw_web_app into ABoroOffice with license-aware access control and enhanced user model integration.

### Key Features
- SSH script approval workflow (pending → approved → executed)
- Email notifications with approval deadline tracking
- Automated reminders (3-tier system)
- Server health checks
- Audit logging
- Excel reporting
- Rating schedule management
- Paramiko-based SSH execution

---

## Architecture

### Models to Create

#### 1. **ApprovalSettings** (Singleton)
```python
- approval_deadline_hours: int (24)
- approval_deadline_minutes: int (15)
- reminder_1_time: TimeField (14:00)
- reminder_2_time: TimeField (20:00)
- reminder_3_time: TimeField (07:00)
- ssh_timeout: int (900 seconds)
- email_from: EmailField
- system_active: BooleanField
```

#### 2. **RatingSchedule**
```python
- display_name: CharField (e.g., "Schulungsumgebung 02")
- server_url_prefix: CharField (e.g., "02")
- ssh_port: IntegerField (1425)
- weekdays: JSONField ([0,1,2,3,4] = Mo-Fr)
- abruf_zeit: TimeField (16:30)
- enabled: BooleanField
- email_recipients: JSONField (for ratings)
- approval_email_recipients: JSONField (for SSH approvals)
- storage_location: CharField (/var/www/.../ratings)
```

#### 3. **ServerHealthCheck**
```python
- server_name: CharField
- server_url: URLField
- ssh_reachable: BooleanField
- url_reachable: BooleanField
- status: CharField ('healthy', 'unreachable', 'unknown')
- last_check: DateTimeField
```

#### 4. **Approval** (Main Model)
```python
- token: UUIDField (unique)
- server_name: CharField
- server_port: IntegerField
- rating_schedule: ForeignKey(RatingSchedule, null=True)
- email_recipients: JSONField
- scheduled_time: DateTimeField
- created_at: DateTimeField (auto_now_add)
- deadline: DateTimeField (07:15 next day)
- status: CharField ('pending', 'approved', 'rejected', 'expired')
- approved_at: DateTimeField (null)
- approved_by: CharField (email/IP/auto)
- approval_method: CharField ('email', 'gui', 'api')
- reminder_1_sent, reminder_2_sent, reminder_3_sent: BooleanField
- executed_at: DateTimeField (null)
- execution_status: CharField ('pending', 'in_progress', 'success', 'failed')
- execution_output: TextField
- execution_error: TextField
- execution_exit_code: IntegerField
- notes: TextField
```

#### 5. **ApprovalReminder**
```python
- approval: ForeignKey(Approval)
- reminder_number: IntegerField (1, 2, or 3)
- reminder_time: CharField ("14:00", "20:00", "07:00")
- sent_at: DateTimeField (auto_now_add)
- recipients: TextField (JSON email list)
```

---

## Integration Points

### 1. User Model (ABoroUser)
- Add fields:
  - `is_approver: BooleanField` (can approve SSH requests)
  - `approval_groups: ManyToManyField` (which servers they approve for)
- Update `can_access_feature()` to check 'approvals' feature

### 2. Licensing System
- Create license feature: `approvals`
- Enable for: ABORO_OFFICE tier and above
- Restrict views and models with `@license_required('approvals')`

### 3. Email System
- Create email templates:
  - `approvals/emails/approval_request.html`
  - `approvals/emails/approval_approved.html`
  - `approvals/emails/approval_rejected.html`
  - `approvals/emails/reminder_1.html` (14:00)
  - `approvals/emails/reminder_2.html` (20:00)
  - `approvals/emails/reminder_3.html` (07:00 next day)

### 4. Celery Tasks
Create task files:
- `send_approval_email(approval_id)`
- `send_reminder_email(approval_id, reminder_number)`
- `execute_ssh_approval(approval_id)`
- `check_approval_deadlines()` (scheduler)
- `check_server_health()`
- `fetch_ratings_for_schedule(schedule_id)`

### 5. Admin Configuration
- ApprovalsAdmin
  - Custom list_display with status indicators
  - Readonly fields for security
  - Actions for manual approval/rejection
  - Filters by status, date range, server

---

## Implementation Steps

### Step 1: Create App Structure ✅
- [ ] Create `apps/approvals/` directory
- [ ] Create `__init__.py`, `apps.py`
- [ ] Create `models.py`, `admin.py`
- [ ] Create `celery_tasks.py`
- [ ] Create `email_service.py`

### Step 2: Implement Models
- [ ] ApprovalSettings (singleton pattern)
- [ ] RatingSchedule model
- [ ] ServerHealthCheck model
- [ ] Approval model with methods
- [ ] ApprovalReminder model
- [ ] Create migrations
- [ ] Run migrations

### Step 3: Create Admin Configuration
- [ ] ApprovalsAdmin with custom actions
- [ ] RatingScheduleAdmin
- [ ] ServerHealthCheckAdmin
- [ ] ApprovalSettingsAdmin

### Step 4: Implement Email Service
- [ ] Create email templates (6 total)
- [ ] Create EmailService class
- [ ] send_approval_email()
- [ ] send_reminder_email()
- [ ] send_approval_approved_email()
- [ ] send_approval_rejected_email()

### Step 5: Implement Celery Tasks
- [ ] Send approval email task
- [ ] Send reminder email tasks
- [ ] SSH execution task (paramiko)
- [ ] Approval deadline checker
- [ ] Server health check task
- [ ] Rating fetch task (optional for Phase 3)

### Step 6: Create API Endpoints
- [ ] GET /api/approvals/ (list pending)
- [ ] GET /api/approvals/{id}/ (detail)
- [ ] POST /api/approvals/{id}/approve/ (approve)
- [ ] POST /api/approvals/{id}/reject/ (reject)
- [ ] GET /api/approvals/{id}/email/{token}/ (email link)

### Step 7: Create Views
- [ ] ApprovalListView (requires login)
- [ ] ApprovalDetailView
- [ ] ApprovalApproveView (email token)
- [ ] ApprovalRejectView
- [ ] ServerHealthCheckView
- [ ] RatingScheduleView

### Step 8: Add Licensing Integration
- [ ] Update core.ABoroUser with approver fields
- [ ] Add license checks to views/APIs
- [ ] Update licensing decorators
- [ ] Test license enforcement

### Step 9: Testing
- [ ] Model tests (CRUD operations)
- [ ] Email generation tests
- [ ] Celery task tests
- [ ] API endpoint tests
- [ ] Workflow tests (approve/reject)
- [ ] Deadline expiry tests

### Step 10: Documentation
- [ ] API documentation
- [ ] Setup guide
- [ ] Configuration guide
- [ ] Email template documentation

---

## Database Schema

### Migrations Required
1. `0001_initial.py` - ApprovalSettings, RatingSchedule, ServerHealthCheck
2. `0002_approval.py` - Approval, ApprovalReminder
3. `0003_aboro_user_approver_fields.py` - Update core.ABoroUser

### Indexes
```python
- Approval: [token], [status, deadline], [server_name, created_at]
- RatingSchedule: [display_name], [enabled]
- ServerHealthCheck: [server_name], [status]
```

---

## Email Workflow

### Approval Request Email
1. **Trigger**: New Approval created
2. **Recipients**: From `approval.email_recipients` or `RatingSchedule.approval_email_recipients`
3. **Content**:
   - Server name
   - Scheduled execution time
   - Deadline (07:15 next day)
   - Approval link with unique token
4. **Headers**: Custom headers for tracking

### Reminder Emails (3-tier)
1. **First (14:00)**: "Genehmigung erforderlich!"
2. **Second (20:00)**: "FINAL ERINNERUNG - Genehmigung erforderlich!"
3. **Third (07:00+1d)**: "LETZTER AUFRUF - Genehmigung erforderlich!"

### Approval Tracking
- Email links use unique token: `/genehmigen/{approval.token}/`
- Method tracked: 'email', 'gui', 'api'
- Approved_by recorded: email address, IP, or 'auto'

---

## SSH Execution Flow

### Prerequisites
- Paramiko library (installed: 4.0.0)
- SSH credentials stored securely
- Server health check passing
- Approval granted

### Execution Steps
1. Check approval status = 'approved'
2. Check server health (is_healthy())
3. Open SSH connection (paramiko.SSHClient)
4. Execute script on remote server
5. Capture output, error, exit code
6. Update approval.execution_status
7. Send completion email
8. Create audit log entry

### Error Handling
- SSH connection failures → execution_status = 'failed'
- Timeout (900s) → execution_status = 'failed'
- Script errors → execution_status = 'failed', capture output
- Log all errors for auditing

---

## Configuration (settings)

```python
# In config/settings/base.py or via environment

APPROVALS = {
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'EMAIL_FROM': 'approvals@aboro.office',
    'EMAIL_HOST': 'smtp.example.com',
    'EMAIL_PORT': 587,
    'EMAIL_USE_TLS': True,
    'SSH_TIMEOUT': 900,  # seconds
    'APPROVAL_DEADLINE_HOURS': 24,
    'APPROVAL_DEADLINE_MINUTES': 15,
}
```

---

## Timeline

| Step | Task | Duration | Status |
|------|------|----------|--------|
| 1 | App structure & models | 2 hours | Pending |
| 2 | Models & migrations | 2 hours | Pending |
| 3 | Admin configuration | 1.5 hours | Pending |
| 4 | Email service & templates | 3 hours | Pending |
| 5 | Celery tasks | 3 hours | Pending |
| 6 | API endpoints | 2.5 hours | Pending |
| 7 | Views & forms | 2 hours | Pending |
| 8 | Licensing integration | 1.5 hours | Pending |
| 9 | Testing suite | 4 hours | Pending |
| 10 | Documentation | 2 hours | Pending |
| **Total** | **Phase 3** | **~23.5 hours** | **Starting** |

---

## Success Criteria

- [ ] All models created and migrated
- [ ] Admin interface fully functional
- [ ] Approval workflow complete (pending → approved → executed)
- [ ] Email notifications sent correctly
- [ ] Reminders sent at configured times
- [ ] SSH execution working with paramiko
- [ ] API endpoints tested
- [ ] License enforcement working
- [ ] 70%+ test coverage
- [ ] Documentation complete
- [ ] No database errors
- [ ] All views require login

---

## Risks & Mitigation

### ⚠️ Security: SSH Credential Storage
- **Risk**: SSH credentials hardcoded or insecure
- **Mitigation**: Use environment variables, encrypted credentials
- **Contingency**: Use SSH key-based auth (no passwords)

### ⚠️ Email Delivery
- **Risk**: Approval emails not delivered
- **Mitigation**: Email logging, retry mechanism
- **Contingency**: Web-based GUI alternative for approvals

### ⚠️ Deadline Management
- **Risk**: Approvals expiring incorrectly
- **Mitigation**: Proper timezone handling (Europe/Berlin), tests
- **Contingency**: Manual extension via admin

### ⚠️ SSH Execution Failures
- **Risk**: SSH commands fail, leaving system in unknown state
- **Mitigation**: Output logging, error tracking, health checks
- **Contingency**: Manual retry with investigation

---

## Next Phase Preparation

**Phase 4 (HelpDesk Integration)** will depend on:
- Approval system operational
- Celery/Redis working
- Email system configured
- Test suite passing

---

## References

- **Source Code**: `C:\Users\aborowczak\PycharmProjects\dokmbw_web_app\approvals\`
- **License Requirements**: ABORO_OFFICE tier or higher
- **Dependencies**: paramiko==4.0.0, celery==5.6.2, redis==7.1.0
- **Related Docs**: PHASE2_SUMMARY.md, QUICKSTART.md

---

**Status**: Ready to start implementation
**Owner**: Phase 3 Implementation
**Last Updated**: 2025-02-03
