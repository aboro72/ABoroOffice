from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from apps.helpdesk.helpdesk_apps.admin_panel.models import EmailLog


class DBConsoleEmailBackend(ConsoleEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        for msg in email_messages:
            try:
                EmailLog.objects.create(
                    subject=msg.subject or '',
                    from_email=msg.from_email or '',
                    to_emails=','.join(msg.to or []),
                    body=msg.body or '',
                    source='console',
                )
            except Exception:
                pass
        return super().send_messages(email_messages)
