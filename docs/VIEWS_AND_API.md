# Phase 3: Views & API Documentation

**Status**: ✅ Priority 3 Complete - Views & URL Routing
**Date**: 2025-02-04

---

## Overview

Implemented web views and API endpoints for the SSH Approval Workflow.

### Components
- ✅ 7 Class-Based Views (CBV)
- ✅ HTML Templates (2 main + base layout)
- ✅ URL Routing (`apps/approvals/urls.py`)
- ✅ JSON API Endpoints (health, statistics, etc.)

---

## Class-Based Views

### 1. ApprovalListView
**URL**: `/approvals/`
**Method**: GET
**Auth**: Required (LoginRequiredMixin)
**Purpose**: Display paginated list of approvals with filtering

**Features**:
- Filter by status (pending, approved, rejected, expired)
- Filter by server name
- Pagination (50 per page)
- Sorted by creation date (newest first)

**Query Parameters**:
```
GET /approvals/?status=pending&server=test-server
```

**Context Variables**:
- `approvals` - Paginated QuerySet
- `status_choices` - List of status options
- `current_status` - Applied status filter
- `current_server` - Applied server filter

---

### 2. ApprovalDetailView
**URL**: `/approvals/<token>/`
**Method**: GET
**Auth**: Required
**Purpose**: Display detailed approval information

**Features**:
- Full approval details
- Reminder history
- Execution status and output
- Server health information
- Approval/rejection buttons (if pending)

**URL Patterns**:
```
/approvals/<uuid:token>/              # By UUID token
/approvals/approval/<int:pk>/         # By approval ID
```

**Context Variables**:
- `approval` - Approval object
- `reminders` - Related ApprovalReminder objects
- `server_health` - ServerHealthCheck object
- `can_approve` - Boolean (can current user approve)
- `hours_remaining` - Float (hours until deadline)

---

### 3. ApprovalApproveView
**URL**: `/approvals/<token>/approve/` or `/approvals/approval/<pk>/approve/`
**Method**: POST
**Auth**: Optional (email token) or Required (web form)
**Purpose**: Approve an approval request

**Features**:
- Approve via email token (no auth needed)
- Approve via web form (staff required)
- Stores approved_by, approved_at, approval_method
- Auto-triggers SSH execution task
- Returns JSON or redirects

**Request**:
```bash
# Via form
POST /approvals/approval/1/approve/

# Via email token (no auth)
POST /approvals/a1b2c3d4-e5f6.../approve/
```

**Response (AJAX)**:
```json
{
    "success": true,
    "message": "Approval granted",
    "status": "approved",
    "approved_by": "admin@example.com",
    "approved_at": "2025-02-04T10:30:00Z"
}
```

---

### 4. ApprovalRejectView
**URL**: `/approvals/approval/<pk>/reject/`
**Method**: POST
**Auth**: Required (staff)
**Purpose**: Reject an approval request

**Features**:
- Staff-only action
- Captures rejection reason
- Stores notes
- Auto-triggers rejection email

**Request**:
```bash
POST /approvals/approval/1/reject/
Form Data:
  reason=Server maintenance planned
```

**Response**:
```json
{
    "success": true,
    "message": "Approval rejected",
    "status": "rejected",
    "reason": "Server maintenance planned"
}
```

---

### 5. ServerHealthCheckView
**URL**: `/approvals/health/` or `/approvals/health/<server_name>/`
**Method**: GET
**Auth**: Required
**Purpose**: Get server health status

**Features**:
- List all servers or get one
- Shows SSH reachability
- Shows URL reachability
- Shows last check time

**Requests**:
```bash
# All servers
GET /approvals/health/

# Specific server
GET /approvals/health/test-server/
```

**Response**:
```json
{
    "success": true,
    "server_name": "test-server",
    "status": "healthy",
    "is_healthy": true,
    "ssh_reachable": true,
    "url_reachable": true,
    "last_check": "2025-02-04T10:30:00Z"
}
```

---

### 6. RatingScheduleStatusView
**URL**: `/approvals/schedule/` or `/approvals/schedule/<schedule_id>/`
**Method**: GET
**Auth**: Required
**Purpose**: Get rating schedule configuration

**Features**:
- List all schedules
- Get specific schedule details
- Shows enabled status
- Shows SSH port and server prefix

**Requests**:
```bash
GET /approvals/schedule/
GET /approvals/schedule/1/
```

**Response**:
```json
{
    "success": true,
    "schedules": [
        {
            "id": 1,
            "display_name": "Schulungsumgebung 01",
            "enabled": true,
            "abruf_zeit": "16:30:00"
        }
    ]
}
```

---

### 7. ApprovalStatisticsView
**URL**: `/approvals/statistics/`
**Method**: GET
**Auth**: Required
**Purpose**: Get approval statistics and metrics

**Features**:
- Total approval counts
- Breakdown by status
- Average approval time
- Last 7 days activity
- Top servers by approval count

**Response**:
```json
{
    "success": true,
    "statistics": {
        "total": 42,
        "by_status": {
            "pending": 3,
            "approved": 28,
            "rejected": 8,
            "expired": 3
        },
        "avg_approval_hours": 2.5,
        "last_week": 12,
        "top_servers": [
            {"server_name": "prod-01", "count": 8},
            {"server_name": "test-01", "count": 5}
        ]
    }
}
```

---

## HTML Templates

### base.html
Master template with:
- Navigation bar with links
- User authentication status
- Message display
- Bootstrap 5 styling
- Font Awesome icons

---

### approval_list.html
Features:
- Approval table with status badges
- Filter form (status + server)
- Pagination controls
- Click-through to detail view
- Responsive design

---

### approval_detail.html
Features:
- Full approval details
- Approval/rejection action buttons
- Execution status and logs
- Reminder history
- Server health indicator
- Email recipients display

---

## URL Routing

All approvals URLs are prefixed with `/approvals/`:

```python
GET     /approvals/                              # List view
GET     /approvals/<token>/                      # Detail view (by token)
GET     /approvals/approval/<pk>/                # Detail view (by ID)
POST    /approvals/<token>/approve/              # Approve (email)
POST    /approvals/approval/<pk>/approve/        # Approve (form)
POST    /approvals/approval/<pk>/reject/         # Reject
GET     /approvals/health/                       # Health check list
GET     /approvals/health/<server_name>/         # Health check detail
GET     /approvals/schedule/                     # Schedule list
GET     /approvals/schedule/<schedule_id>/       # Schedule detail
GET     /approvals/statistics/                   # Statistics
```

---

## Authentication & Permissions

### Public Access (No Auth)
- Approval approval via email token: `/<token>/approve/`

### Requires Login
- All other views and endpoints

### Requires Staff Status
- Approval rejection
- Future: detailed management views

### TODO: Licensing Integration
- Check `is_approver` field on user
- Check approval groups
- Enforce license tier

---

## API Response Format

All JSON endpoints follow this format:

**Success**:
```json
{
    "success": true,
    "message": "...",
    "data": {...}
}
```

**Error**:
```json
{
    "success": false,
    "error": "Error message"
}
```

**HTTP Status Codes**:
- 200 - OK
- 302 - Redirect (unauthenticated)
- 400 - Bad request
- 403 - Forbidden
- 404 - Not found
- 500 - Server error

---

## AJAX Integration

Views detect AJAX requests via `X-Requested-With` header:

```javascript
// JavaScript example
fetch('/approvals/approval/1/approve/', {
    method: 'POST',
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
    }
})
.then(r => r.json())
.then(data => {
    if (data.success) {
        // Update UI
        location.reload();
    } else {
        // Show error
        alert(data.error);
    }
});
```

---

## Testing

### Manual Testing
```python
python manage.py runserver
# Visit http://localhost:8000/
# Navigate to /approvals/
```

### Command Line Testing
```bash
# List view
curl http://localhost:8000/approvals/

# Health check
curl http://localhost:8000/approvals/health/

# Statistics
curl http://localhost:8000/approvals/statistics/
```

---

## Next Steps (Priority 4)

### License Integration
- [ ] Add `is_approver` field to ABoroUser
- [ ] Create `approval_groups` M2M relationship
- [ ] Add license checks to views
- [ ] Implement `@license_required` decorator

### Estimated**: 1.5 hours

---

## Metrics

| Component | Lines | Status |
|-----------|-------|--------|
| views.py | 450+ | ✅ Complete |
| urls.py | 25 | ✅ Complete |
| Templates | 350+ | ✅ Complete |
| base.html | 100+ | ✅ Complete |
| home.html | 70+ | ✅ Complete |
| **Total** | **1000+** | **✅** |

---

**Last Updated**: 2025-02-04
**Phase 3 Progress**: 65% → 80%
**Time Spent**: ~2 hours
**Remaining**: License Integration (1.5h) + Tests (4h) + Polish (2h)
