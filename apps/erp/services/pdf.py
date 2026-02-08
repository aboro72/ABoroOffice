from io import BytesIO
from typing import Iterable
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.utils import timezone
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


PAGE_WIDTH, PAGE_HEIGHT = A4


def _draw_header(c: canvas.Canvas, settings_obj: SystemSettings) -> float:
    y = PAGE_HEIGHT - 20 * mm
    logo = settings_obj.logo
    if logo and hasattr(logo, 'path'):
        try:
            c.drawImage(logo.path, 20 * mm, y - 18 * mm, width=40 * mm, height=18 * mm, preserveAspectRatio=True)
        except Exception:
            pass
    c.setFont('Helvetica-Bold', 14)
    c.drawString(70 * mm, y - 4 * mm, settings_obj.company_name or '')
    c.setFont('Helvetica', 9)
    lines = [
        settings_obj.company_address or '',
        f"{settings_obj.company_postal_code or ''} {settings_obj.company_city or ''}".strip(),
        settings_obj.company_country or '',
        settings_obj.company_email or '',
    ]
    lines = [line for line in lines if line]
    for i, line in enumerate(lines):
        c.drawString(70 * mm, y - (9 + i * 4) * mm, line)
    return y - (18 + max(1, len(lines)) * 4) * mm


def _draw_sender_line(c: canvas.Canvas, settings_obj: SystemSettings) -> None:
    sender_parts = [
        settings_obj.company_name,
        settings_obj.company_address,
        f"{settings_obj.company_postal_code or ''} {settings_obj.company_city or ''}".strip(),
    ]
    sender_parts = [p for p in sender_parts if p]
    sender_line = " · ".join(sender_parts)
    if sender_line:
        c.setFont('Helvetica', 8)
        c.drawString(20 * mm, PAGE_HEIGHT - 38 * mm, sender_line)


def _draw_address_window(c: canvas.Canvas, recipient_lines: Iterable[str]) -> float:
    # DIN 5008 window approx: 45mm from top, 20mm from left
    x = 20 * mm
    y = PAGE_HEIGHT - 45 * mm
    c.setFont('Helvetica', 10)
    for i, line in enumerate(recipient_lines):
        c.drawString(x, y - i * 5 * mm, line)
    return y - (len(list(recipient_lines)) * 5 * mm)


def _draw_fold_marks(c: canvas.Canvas) -> None:
    # fold marks on left margin (approx A4: 105mm and 210mm)
    x = 5 * mm
    for mm_from_top in (105, 210):
        y = PAGE_HEIGHT - mm_from_top * mm
        c.line(x, y, x + 5 * mm, y)


def _draw_title(c: canvas.Canvas, title: str, y: float) -> float:
    c.setFont('Helvetica-Bold', 12)
    c.drawString(20 * mm, y, title)
    return y - 8 * mm


def _draw_paragraph(c: canvas.Canvas, lines: Iterable[str], y: float) -> float:
    c.setFont('Helvetica', 10)
    for line in lines:
        if y < 20 * mm:
            c.showPage()
            y = PAGE_HEIGHT - 20 * mm
            c.setFont('Helvetica', 10)
        c.drawString(20 * mm, y, line)
        y -= 5 * mm
    return y


def _draw_table(c: canvas.Canvas, headers: list[str], rows: list[list[str]], y: float) -> float:
    col_widths = [12 * mm, 88 * mm, 18 * mm, 25 * mm, 25 * mm]
    x = 20 * mm
    c.setFont('Helvetica-Bold', 9)
    for i, h in enumerate(headers):
        c.drawString(x, y, h)
        x += col_widths[i]
    y -= 4 * mm
    c.line(20 * mm, y, PAGE_WIDTH - 20 * mm, y)
    y -= 4 * mm

    c.setFont('Helvetica', 9)
    for row in rows:
        if y < 35 * mm:
            c.showPage()
            y = PAGE_HEIGHT - 20 * mm
        x = 20 * mm
        for i, cell in enumerate(row):
            value = (cell or '')
            if i == 1 and len(value) > 60:
                value = value[:57] + '...'
            c.drawString(x, y, value)
            x += col_widths[i]
        y -= 5 * mm
    return y - 2 * mm


def _payment_lines(settings_obj: SystemSettings) -> list[str]:
    lines = []
    if settings_obj.company_bank_name:
        lines.append(f"Bank: {settings_obj.company_bank_name}")
    if settings_obj.company_iban:
        lines.append(f"IBAN: {settings_obj.company_iban}")
    if settings_obj.company_bic:
        lines.append(f"BIC: {settings_obj.company_bic}")
    return lines


def _draw_payment_box(c: canvas.Canvas, lines: list[str]) -> None:
    if not lines:
        return
    box_width = 80 * mm
    box_height = max(18 * mm, (len(lines) + 1) * 5 * mm)
    x = PAGE_WIDTH - box_width - 20 * mm
    y = 35 * mm
    c.rect(x, y, box_width, box_height)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(x + 4 * mm, y + box_height - 6 * mm, 'Zahlungsinformationen')
    c.setFont('Helvetica', 9)
    for i, line in enumerate(lines):
        c.drawString(x + 4 * mm, y + box_height - (11 + i * 4) * mm, line)


def build_letter_pdf(title: str, body_lines: Iterable[str]) -> bytes:
    settings_obj = SystemSettings.get_settings()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = _draw_header(c, settings_obj)
    y -= 6 * mm
    y = _draw_title(c, title, y)
    y = _draw_paragraph(c, body_lines, y)
    c.setFont('Helvetica-Oblique', 8)
    c.drawRightString(PAGE_WIDTH - 20 * mm, 15 * mm, timezone.now().strftime('%Y-%m-%d %H:%M'))
    c.showPage()
    c.save()
    return buffer.getvalue()


def build_invoice_pdf(invoice) -> bytes:
    settings_obj = SystemSettings.get_settings()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_header(c, settings_obj)
    _draw_fold_marks(c)
    _draw_sender_line(c, settings_obj)

    customer = invoice.order.customer if invoice.order else None
    recipient_lines = []
    if customer:
        recipient_lines.append(customer.name)
        if customer.address:
            recipient_lines.append(customer.address)
    _draw_address_window(c, recipient_lines)

    y = PAGE_HEIGHT - 80 * mm
    y = _draw_title(c, f"Rechnung {invoice.number}", y)

    meta_lines = [
        f"Datum: {invoice.issue_date}",
        f"Faellig: {invoice.due_date or '-'}",
    ]
    if customer and customer.email:
        meta_lines.append(f"E-Mail: {customer.email}")

    y = _draw_paragraph(c, meta_lines, y)
    y -= 2 * mm

    rows = []
    for idx, item in enumerate(invoice.order.items.all(), start=1):
        rows.append([
            str(idx),
            item.product.name if item.product else 'Position',
            str(item.quantity),
            f"{item.unit_price:.2f}",
            f"{Decimal(str(item.line_total())):.2f}",
        ])

    y = _draw_table(c, ['Pos', 'Beschreibung', 'Menge', 'Einzel', 'Gesamt'], rows, y)

    totals = [
        f"Netto: {invoice.net_amount:.2f} EUR",
        f"MwSt ({invoice.tax_rate:.0f}%): {invoice.tax_amount:.2f} EUR",
        f"Brutto: {invoice.total_amount:.2f} EUR",
        f"Zahlungsziel: {settings_obj.invoice_payment_days} Tage",
    ]
    y = _draw_paragraph(c, totals, y)

    payment = _payment_lines(settings_obj)
    if payment:
        _draw_payment_box(c, payment)

    if invoice.notes:
        y = _draw_paragraph(c, ['Hinweise:'] + invoice.notes.splitlines(), y)

    c.setFont('Helvetica-Oblique', 8)
    c.drawRightString(PAGE_WIDTH - 20 * mm, 15 * mm, timezone.now().strftime('%Y-%m-%d %H:%M'))
    c.showPage()
    c.save()
    return buffer.getvalue()


def build_dunning_pdf(dunning) -> bytes:
    settings_obj = SystemSettings.get_settings()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_header(c, settings_obj)
    _draw_fold_marks(c)
    _draw_sender_line(c, settings_obj)

    invoice = dunning.invoice
    customer = invoice.order.customer if invoice.order else None
    recipient_lines = []
    if customer:
        recipient_lines.append(customer.name)
        if customer.address:
            recipient_lines.append(customer.address)
    _draw_address_window(c, recipient_lines)

    y = PAGE_HEIGHT - 80 * mm
    y = _draw_title(c, f"Mahnung {dunning.number}", y)

    meta_lines = [
        f"Rechnung: {invoice.number}",
        f"Betrag: {invoice.total_amount:.2f} EUR",
        f"Faellig seit: {invoice.due_date or '-'}",
        f"Stufe: {dunning.level}",
    ]
    y = _draw_paragraph(c, meta_lines, y)

    body_lines = (dunning.letter_text or '').splitlines()
    if body_lines:
        y = _draw_paragraph(c, body_lines, y)

    payment = _payment_lines(settings_obj)
    if payment:
        _draw_payment_box(c, payment)

    c.setFont('Helvetica-Oblique', 8)
    c.drawRightString(PAGE_WIDTH - 20 * mm, 15 * mm, timezone.now().strftime('%Y-%m-%d %H:%M'))
    c.showPage()
    c.save()
    return buffer.getvalue()
