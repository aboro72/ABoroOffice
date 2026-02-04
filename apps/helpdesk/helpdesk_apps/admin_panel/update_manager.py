"""
Update Manager - Handles automatic updates from GitHub
Downloads only changed files and updates the system
"""

import os
import json
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from django.db import models

logger = logging.getLogger(__name__)

# GitHub configuration
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'aborowczak/HelpDesk')
GITHUB_BRANCH = os.environ.get('GITHUB_BRANCH', 'main')
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}'
GITHUB_RAW_URL = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}'

# Files that should never be auto-updated (config files)
PROTECTED_FILES = {
    '.env',
    'helpdesk/settings.py',
    'db.sqlite3',
    'manage.py',
}

# Files to check for updates (relative to project root)
MONITORED_FILES = {
    # Core application files
    'apps/admin_panel/models.py',
    'apps/admin_panel/views.py',
    'apps/admin_panel/forms.py',
    'apps/admin_panel/signals.py',
    'apps/admin_panel/settings_helper.py',
    'apps/tickets/models.py',
    'apps/tickets/views.py',
    'apps/tickets/email_handler.py',
    'apps/tickets/management/commands/process_emails.py',
    'apps/tickets/tasks.py',
    'apps/main/forms.py',
    'apps/main/views.py',
    # Templates
    'templates/base.html',
    'templates/main/admin_settings.html',
    # Static files
    'static/css/theme.css',
    # Documentation
    'START_HERE.md',
    'EMAIL_TO_TICKETS_README.md',
    'IMAP_UI_SETUP.md',
    'SCHEDULER_SETUP.md',
    'EMAIL_SETUP_QUICK_START.md',
}


class UpdateChecker:
    """Check for available updates"""

    def __init__(self):
        self.base_path = Path(settings.BASE_DIR)
        self.cache_key = 'helpdesk_update_check'
        self.cache_timeout = 3600  # 1 hour

    def get_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {str(e)}")
            return None

    def get_github_file_hash(self, file_path):
        """Get SHA256 hash of file from GitHub"""
        try:
            url = f'{GITHUB_API_URL}/contents/{file_path}'
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if 'sha' in data:
                    return data['sha']
            return None
        except Exception as e:
            logger.error(f"Error getting GitHub hash for {file_path}: {str(e)}")
            return None

    def check_for_updates(self, force=False):
        """Check if updates are available"""
        # Check cache first
        if not force:
            cached = cache.get(self.cache_key)
            if cached is not None:
                return cached

        try:
            updates = {}

            for file_path in MONITORED_FILES:
                local_path = self.base_path / file_path

                # Skip if file doesn't exist locally
                if not local_path.exists():
                    continue

                # Skip protected files
                if file_path in PROTECTED_FILES:
                    continue

                local_hash = self.get_file_hash(local_path)
                if not local_hash:
                    continue

                # Get GitHub file info
                try:
                    url = f'{GITHUB_API_URL}/contents/{file_path}'
                    response = requests.get(url, timeout=5)

                    if response.status_code == 200:
                        data = response.json()
                        github_hash = data.get('sha')

                        # Git uses a special hash format, compare content instead
                        if self._file_needs_update(local_path, file_path):
                            updates[file_path] = {
                                'local_hash': local_hash,
                                'github_hash': github_hash,
                                'timestamp': datetime.now().isoformat()
                            }
                except Exception as e:
                    logger.warning(f"Could not check {file_path}: {str(e)}")
                    continue

            result = {
                'has_updates': len(updates) > 0,
                'updates': updates,
                'file_count': len(updates),
                'checked_at': datetime.now().isoformat(),
                'branch': GITHUB_BRANCH,
                'repo': GITHUB_REPO
            }

            # Cache the result
            cache.set(self.cache_key, result, self.cache_timeout)
            return result

        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            return {
                'has_updates': False,
                'updates': {},
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }

    def _file_needs_update(self, local_path, file_path):
        """Check if a file needs updating by comparing content"""
        try:
            # Get content from GitHub
            url = f'{GITHUB_RAW_URL}/{file_path}'
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return False

            github_content = response.content

            # Get local content
            with open(local_path, 'rb') as f:
                local_content = f.read()

            # Compare
            return github_content != local_content

        except Exception as e:
            logger.warning(f"Error comparing {file_path}: {str(e)}")
            return False


class UpdateDownloader:
    """Download and install updates"""

    def __init__(self):
        self.base_path = Path(settings.BASE_DIR)
        self.backup_dir = self.base_path / '.update_backups'
        self.backup_dir.mkdir(exist_ok=True)

    def download_file(self, file_path):
        """Download a file from GitHub"""
        try:
            url = f'{GITHUB_RAW_URL}/{file_path}'
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                raise Exception(f"GitHub returned {response.status_code}")

            return response.content

        except Exception as e:
            logger.error(f"Error downloading {file_path}: {str(e)}")
            return None

    def backup_file(self, file_path):
        """Create backup of file before updating"""
        try:
            local_path = self.base_path / file_path

            if not local_path.exists():
                return None

            backup_path = self.backup_dir / f"{file_path.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    dst.write(src.read())

            logger.info(f"Backed up {file_path} to {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Error backing up {file_path}: {str(e)}")
            return None

    def install_file(self, file_path, content):
        """Install updated file"""
        try:
            # Backup original
            self.backup_file(file_path)

            # Write new content
            local_path = self.base_path / file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, 'wb') as f:
                f.write(content)

            logger.info(f"Updated {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error installing {file_path}: {str(e)}")
            return False

    def install_updates(self, file_list):
        """Download and install a list of files"""
        results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'timestamp': datetime.now().isoformat()
        }

        for file_path in file_list:
            # Skip protected files
            if file_path in PROTECTED_FILES:
                results['skipped'].append({
                    'file': file_path,
                    'reason': 'Protected file'
                })
                continue

            # Download file
            content = self.download_file(file_path)
            if not content:
                results['failed'].append(file_path)
                continue

            # Install file
            if self.install_file(file_path, content):
                results['success'].append(file_path)
            else:
                results['failed'].append(file_path)

        return results


class UpdateNotification(models.Model):
    """Store update notifications"""

    title = models.CharField(max_length=255)
    description = models.TextField()
    version = models.CharField(max_length=50)
    available_files = models.JSONField(default=list)
    installed = models.BooleanField(default=False)
    installed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Update Notification'
        verbose_name_plural = 'Update Notifications'
        ordering = ['-created_at']

    def __str__(self):
        status = 'Installed' if self.installed else 'Available'
        return f"{self.version} - {status}"

    @classmethod
    def create_from_check(cls, update_info):
        """Create notification from update check result"""
        try:
            if not update_info.get('has_updates'):
                return None

            files = list(update_info.get('updates', {}).keys())

            notification = cls.objects.create(
                title=f"Update Available - {len(files)} files changed",
                description=f"Found {len(files)} updated files in {update_info.get('repo')}",
                version=update_info.get('checked_at', 'Unknown'),
                available_files=files
            )

            logger.info(f"Created update notification for {len(files)} files")
            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None


def check_and_notify_updates():
    """Celery task to check for updates and notify"""
    try:
        checker = UpdateChecker()
        update_info = checker.check_for_updates()

        if update_info.get('has_updates'):
            # Create notification
            notification = UpdateNotification.create_from_check(update_info)
            return {
                'status': 'update_available',
                'notification_id': notification.id if notification else None,
                'file_count': update_info.get('file_count', 0)
            }
        else:
            return {
                'status': 'up_to_date',
                'checked_at': update_info.get('checked_at')
            }

    except Exception as e:
        logger.error(f"Error in check_and_notify_updates: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def install_updates_task(notification_id):
    """Celery task to install updates"""
    try:
        notification = UpdateNotification.objects.get(id=notification_id)

        if notification.installed:
            return {
                'status': 'already_installed',
                'notification_id': notification_id
            }

        downloader = UpdateDownloader()
        results = downloader.install_updates(notification.available_files)

        # Update notification
        notification.installed = True
        notification.installed_at = datetime.now()
        notification.save()

        logger.info(f"Updates installed: {len(results['success'])} success, {len(results['failed'])} failed")

        return {
            'status': 'success',
            'results': results,
            'notification_id': notification_id
        }

    except Exception as e:
        logger.error(f"Error installing updates: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
