from django.core.mail import send_mail
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.erp.models import Invoice


def _render_template(template: str, mapping: dict) -> str:
    try:
        return template.format_map(mapping)
    except Exception:
        return template


def build_invoice_letter(invoice: Invoice) -> str:
    settings_obj = SystemSettings.get_settings()
    customer = invoice.order.customer if invoice.order else None

    sender_lines = [
        settings_obj.company_name,
        settings_obj.company_address,
        f"{settings_obj.company_postal_code} {settings_obj.company_city}".strip(),
        settings_obj.company_country,
    ]
    sender_lines = [line for line in sender_lines if line]
    sender = "\n".join(sender_lines)

    recipient_lines = []
    if customer:
        recipient_lines.append(customer.name)
        if customer.address:
            recipient_lines.append(customer.address)
    recipient = "\n".join(recipient_lines)

    body = [
        sender,
        "",
        recipient,
        "",
        f"Rechnung {invoice.number}",
        f"Datum: {invoice.issue_date}",
        f"Betrag: {invoice.total_amount} EUR",
        "",
        "Bitte begleichen Sie den Betrag fristgerecht.",
    ]
    payment_lines = []
    if settings_obj.company_bank_name:
        payment_lines.append(f"Bank: {settings_obj.company_bank_name}")
    if settings_obj.company_iban:
        payment_lines.append(f"IBAN: {settings_obj.company_iban}")
    if settings_obj.company_bic:
        payment_lines.append(f"BIC: {settings_obj.company_bic}")
    if payment_lines:
        body.extend(["", "Zahlungsdaten:"] + payment_lines)
    return "\n".join(body).strip()


def send_invoice_email(invoice: Invoice) -> bool:
    settings_obj = SystemSettings.get_settings()
    if not settings_obj.send_email_notifications:
        return False

    customer = invoice.order.customer if invoice.order else None
    if not customer or not customer.email:
        return False

    mapping = {
        'invoice_number': invoice.number,
        'amount': f"{invoice.total_amount} EUR",
        'due_date': invoice.due_date or '-',
        'customer_name': customer.name,
        'company_name': settings_obj.company_name,
    }
    subject_tpl = settings_obj.invoice_email_subject_template or f"Rechnung {invoice.number}"
    body_tpl = settings_obj.invoice_email_body_template or ""
    subject = _render_template(subject_tpl, mapping)
    body = _render_template(body_tpl, mapping) if body_tpl else build_invoice_letter(invoice)
    from_email = settings_obj.company_email or settings_obj.smtp_username or None

    send_mail(subject, body, from_email, [customer.email], fail_silently=True)
    return True
