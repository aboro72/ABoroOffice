# Cloud Storage API (Cloude)

**Base URL:** `/cloudstorage/api/`
**Auth:** Session auth (logged-in user) or DRF auth (if configured). Most endpoints require authentication.

## Core Resources (ViewSets)
- `GET /cloudstorage/api/files/` list files
- `POST /cloudstorage/api/files/` create file metadata
- `GET /cloudstorage/api/files/{id}/` file details
- `PATCH /cloudstorage/api/files/{id}/` update
- `DELETE /cloudstorage/api/files/{id}/` delete

- `GET /cloudstorage/api/folders/` list folders
- `POST /cloudstorage/api/folders/` create folder
- `GET /cloudstorage/api/folders/{id}/`
- `PATCH /cloudstorage/api/folders/{id}/`
- `DELETE /cloudstorage/api/folders/{id}/`

- `GET /cloudstorage/api/shares/` list shares
- `POST /cloudstorage/api/shares/` create share

- `GET /cloudstorage/api/public-links/` list public links
- `POST /cloudstorage/api/public-links/` create public link

- `GET /cloudstorage/api/users/` current user (limited)
- `GET /cloudstorage/api/activities/` activity log

## File Operations
- `POST /cloudstorage/api/files/upload/` upload file (multipart)
- `GET /cloudstorage/api/files/{id}/download/` download file
- `GET /cloudstorage/api/files/{id}/versions/` list versions
- `POST /cloudstorage/api/files/{id}/restore/` restore version

## Storage
- `GET /cloudstorage/api/storage/stats/` storage stats
- `GET /cloudstorage/api/storage/quota/` quota information

## Search
- `GET /cloudstorage/api/search/?q=term`

## Notifications
- `GET /cloudstorage/api/notifications/`
- `POST /cloudstorage/api/notifications/{id}/read/`

## Sharing Helpers
- `POST /cloudstorage/api/shares/{id}/permissions/`
- `POST /cloudstorage/api/public-links/{id}/password/`

## Plugins (Admin Only)
- `POST /cloudstorage/api/plugins/discover/`
- `POST /cloudstorage/api/plugins/{id}/activate/`
- `POST /cloudstorage/api/plugins/{id}/deactivate/`
- `GET|POST /cloudstorage/api/plugins/{id}/settings/`

## Example: Upload
```bash
curl -X POST -H "X-CSRFToken: <token>" -F "file=@/path/to/file.pdf"   http://127.0.0.1:8000/cloudstorage/api/files/upload/
```
