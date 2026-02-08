import re
from urllib.parse import urljoin, urlparse
import requests
from django.utils import timezone
from apps.crm.models import Account, Contact, Lead, LeadStaging


def _normalize(text):
    return (text or "").strip().lower()


def _find_account(company):
    if not company:
        return None
    return Account.objects.filter(name__iexact=company).first()


def _find_contact_for_account(account):
    if not account:
        return None
    return account.contacts.first()


def _find_contact_by_company(company):
    if not company:
        return None
    return Contact.objects.filter(account__name__iexact=company).first()


def _find_existing_lead(company):
    if not company:
        return None
    return Lead.objects.filter(company__iexact=company).first()


def _normalize_url(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if not parsed.scheme:
        value = f"https://{value}"
        parsed = urlparse(value)
    if not parsed.netloc:
        return ""
    return value


def _fetch_url(url: str) -> str:
    headers = {
        "User-Agent": "ABoroOfficeCRM/1.0 (+https://example.invalid)",
        "Accept": "text/html,application/xhtml+xml",
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text[:1_000_000]


def _extract_emails(text: str):
    if not text:
        return []
    pattern = r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"
    return list({e.lower() for e in re.findall(pattern, text, flags=re.IGNORECASE)})


def _extract_links(text: str, base_url: str):
    if not text:
        return []
    links = re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.IGNORECASE)
    cleaned = []
    for link in links:
        if link.startswith("mailto:"):
            continue
        if link.startswith("#"):
            continue
        full = urljoin(base_url, link)
        cleaned.append(full)
    return cleaned


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    cleaned = re.sub(r"(?is)<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?is)</p>|</div>|</li>", "\n", cleaned)
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"[ \t\r\f\v]+", " ", cleaned)
    cleaned = re.sub(r"\n\s+", "\n", cleaned)
    return cleaned.strip()


def _extract_phones(text: str):
    if not text:
        return []
    pattern = r"(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{2,5}\)?[\s\-\.]?)?\d{3,4}[\s\-\.]?\d{3,5}"
    matches = re.findall(pattern, text)
    cleaned = []
    for value in matches:
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) < 6:
            continue
        if re.fullmatch(r"0+", re.sub(r"\D", "", value) or "0"):
            continue
        cleaned.append(value)
    # de-dup while preserving order
    seen = set()
    result = []
    for item in cleaned:
        key = item.replace(" ", "")
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _extract_address(text: str):
    if not text:
        return ""
    patterns = [
        r"([A-Za-zÄÖÜäöüß\.\- ]+\s+\d{1,4}[a-zA-Z]?)\s*(?:,|\n)\s*(\d{5}\s+[A-Za-zÄÖÜäöüß\.\- ]+)",
        r"(?:Adresse|Anschrift)\s*[:\-]?\s*([^\n\r]{10,120})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        if len(match.groups()) >= 2:
            candidate = f"{match.group(1).strip()}, {match.group(2).strip()}"
        else:
            candidate = match.group(1).strip()
        if re.search(r"\b\d{5}\b", candidate):
            return candidate
    return ""


def _find_email_from_site(website: str):
    url = _normalize_url(website)
    if not url:
        return ""
    try:
        html = _fetch_url(url)
    except Exception:
        return ""
    emails = _extract_emails(html)
    if emails:
        return emails[0]
    candidates = []
    for link in _extract_links(html, url):
        if any(token in link.lower() for token in ["kontakt", "contact", "impressum", "imprint"]):
            candidates.append(link)
    for link in candidates[:3]:
        try:
            sub_html = _fetch_url(link)
        except Exception:
            continue
        emails = _extract_emails(sub_html)
        if emails:
            return emails[0]
    return ""


def enrich_lead_from_website(lead: Lead):
    if not lead.website:
        return False
    url = _normalize_url(lead.website)
    if not url:
        return False
    try:
        html = _fetch_url(url)
    except Exception:
        return False

    updated = False
    page_text = _html_to_text(html)
    pages = [(url, page_text)]
    for link in _extract_links(html, url):
        if any(token in link.lower() for token in ["kontakt", "contact", "impressum", "imprint"]):
            try:
                sub_html = _fetch_url(link)
                pages.append((link, _html_to_text(sub_html)))
            except Exception:
                continue

    if not lead.email:
        for _, text in pages:
            emails = _extract_emails(text)
            if emails:
                lead.email = emails[0]
                updated = True
                break

    if not lead.phone:
        for _, text in pages:
            phones = _extract_phones(text)
            if phones:
                lead.phone = phones[0]
                updated = True
                break

    if not lead.address:
        for _, text in pages:
            address = _extract_address(text)
            if address:
                lead.address = address
                updated = True
                break

    if lead.phone and re.fullmatch(r"0+", re.sub(r"\D", "", lead.phone) or "0"):
        lead.phone = ""
        updated = True
    if lead.address and "<" in lead.address:
        lead.address = ""
        updated = True

    if updated:
        lead.save(update_fields=['email', 'phone', 'address', 'updated_at'])
    return updated


def enrich_staging_item(item: LeadStaging):
    notes = []
    try:
        account = _find_account(item.company)
        contact = _find_contact_for_account(account) or _find_contact_by_company(item.company)
        existing_lead = _find_existing_lead(item.company)

        if not item.phone:
            if account and account.phone:
                item.phone = account.phone
                notes.append("Telefon aus Account übernommen")
            elif contact and contact.phone:
                item.phone = contact.phone
                notes.append("Telefon aus Kontakt übernommen")
            elif existing_lead and existing_lead.phone:
                item.phone = existing_lead.phone
                notes.append("Telefon aus bestehendem Lead übernommen")

        if not item.email:
            if account and account.email:
                item.email = account.email
                notes.append("E-Mail aus Account übernommen")
            elif contact and contact.email:
                item.email = contact.email
                notes.append("E-Mail aus Kontakt übernommen")
            elif existing_lead and existing_lead.email:
                item.email = existing_lead.email
                notes.append("E-Mail aus bestehendem Lead übernommen")
            else:
                website = ""
                if isinstance(item.raw_data, dict):
                    website = item.raw_data.get("website") or item.raw_data.get("source_url") or ""
                if not website and account and account.website:
                    website = account.website
                if website:
                    email = _find_email_from_site(website)
                    if email:
                        item.email = email
                        notes.append("E-Mail von Website gefunden")

        if not item.name:
            if contact and (contact.first_name or contact.last_name):
                item.name = f"{contact.first_name} {contact.last_name}".strip()
                notes.append("Name aus Kontakt übernommen")

        if not item.lead_source:
            item.lead_source = 'other'
        if not item.lead_status:
            item.lead_status = 'new'

        if item.name and item.company and item.email and item.phone:
            item.status = 'ready'
        else:
            item.status = 'incomplete'

        item.enrichment_status = 'enriched' if notes else 'no_match'
        item.enrichment_notes = "; ".join(notes)
        item.enriched_at = timezone.now()
        item.save()
        return True
    except Exception as exc:
        item.enrichment_status = 'error'
        item.enrichment_notes = str(exc)
        item.enriched_at = timezone.now()
        item.save(update_fields=['enrichment_status', 'enrichment_notes', 'enriched_at'])
        return False


def enrich_queryset(qs):
    enriched = 0
    for item in qs:
        if enrich_staging_item(item):
            enriched += 1
    return enriched
