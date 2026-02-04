"""
Django Management Command: Check for updates
Checks GitHub for available updates and notifies admin
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.helpdesk.helpdesk_apps.admin_panel.update_manager import (
    UpdateChecker, UpdateDownloader, UpdateNotification,
    check_and_notify_updates, install_updates_task
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for available updates from GitHub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--install',
            action='store_true',
            help='Automatically install available updates',
        )

        parser.add_argument(
            '--notification-id',
            type=int,
            help='Install updates for specific notification ID',
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update check (ignore cache)',
        )

        parser.add_argument(
            '--list-files',
            action='store_true',
            help='List files that would be updated',
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbosity', 1) > 1

        if options['install'] and options['notification_id']:
            self.install_specific_update(options['notification_id'])
        elif options['install']:
            self.check_and_install_updates()
        else:
            self.check_updates(options['force'], options['list_files'])

    def check_updates(self, force=False, list_files=False):
        """Check for available updates"""
        self.stdout.write(self.style.SUCCESS('Checking for updates...'))
        self.stdout.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]')
        self.stdout.write('')

        try:
            checker = UpdateChecker()
            result = checker.check_for_updates(force=force)

            if result.get('error'):
                self.stdout.write(
                    self.style.ERROR(f'Error checking updates: {result["error"]}')
                )
                return

            if result.get('has_updates'):
                self.stdout.write(
                    self.style.SUCCESS(f'Updates available: {result["file_count"]} files')
                )
                self.stdout.write(f'Branch: {result["branch"]}')
                self.stdout.write(f'Repository: {result["repo"]}')
                self.stdout.write('')

                if list_files:
                    self.stdout.write(self.style.WARNING('Files to update:'))
                    for file_path in result['updates'].keys():
                        self.stdout.write(f'  - {file_path}')
                    self.stdout.write('')

                self.stdout.write(self.style.WARNING('Run with --install to apply updates'))

            else:
                self.stdout.write(
                    self.style.SUCCESS('System is up to date!')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            logger.error(f"Update check error: {str(e)}")

    def check_and_install_updates(self):
        """Check for updates and automatically install"""
        self.stdout.write(self.style.SUCCESS('Checking for updates and installing...'))
        self.stdout.write('')

        try:
            # Check for updates
            checker = UpdateChecker()
            result = checker.check_for_updates(force=True)

            if result.get('error'):
                self.stdout.write(
                    self.style.ERROR(f'Error: {result["error"]}')
                )
                return

            if not result.get('has_updates'):
                self.stdout.write(
                    self.style.SUCCESS('System is already up to date!')
                )
                return

            # Create notification
            notification = UpdateNotification.create_from_check(result)

            if not notification:
                self.stdout.write(
                    self.style.ERROR('Failed to create update notification')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f'Found {result["file_count"]} updated files'
                )
            )

            # Download and install
            self.stdout.write(self.style.WARNING('Downloading and installing files...'))
            self.stdout.write('')

            downloader = UpdateDownloader()
            install_results = downloader.install_updates(result['updates'].keys())

            # Print results
            if install_results['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {len(install_results["success"])} files:')
                )
                for file_path in install_results['success']:
                    self.stdout.write(f'  + {file_path}')
                self.stdout.write('')

            if install_results['failed']:
                self.stdout.write(
                    self.style.ERROR(f'Failed to update {len(install_results["failed"])} files:')
                )
                for file_path in install_results['failed']:
                    self.stdout.write(f'  - {file_path}')
                self.stdout.write('')

            if install_results['skipped']:
                self.stdout.write(
                    self.style.WARNING(f'Skipped {len(install_results["skipped"])} protected files')
                )
                self.stdout.write('')

            # Update notification
            notification.installed = True
            notification.installed_at = timezone.now()
            notification.save()

            self.stdout.write(
                self.style.SUCCESS('Update installation completed!')
            )

            if install_results['failed']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Note: {len(install_results["failed"])} files failed to update. '
                        'Check logs for details.'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during installation: {str(e)}')
            )
            logger.error(f"Update installation error: {str(e)}")

    def install_specific_update(self, notification_id):
        """Install updates for specific notification"""
        self.stdout.write(self.style.SUCCESS(f'Installing updates for notification {notification_id}...'))
        self.stdout.write('')

        try:
            notification = UpdateNotification.objects.get(id=notification_id)

            if notification.installed:
                self.stdout.write(
                    self.style.WARNING('This update has already been installed.')
                )
                return

            # Download and install
            downloader = UpdateDownloader()
            install_results = downloader.install_updates(notification.available_files)

            # Print results
            if install_results['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {len(install_results["success"])} files')
                )

            if install_results['failed']:
                self.stdout.write(
                    self.style.ERROR(f'Failed to update {len(install_results["failed"])} files')
                )

            # Update notification
            notification.installed = True
            notification.installed_at = timezone.now()
            notification.save()

            self.stdout.write(
                self.style.SUCCESS('Installation completed!')
            )

        except UpdateNotification.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Notification {notification_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            logger.error(f"Error installing update: {str(e)}")
