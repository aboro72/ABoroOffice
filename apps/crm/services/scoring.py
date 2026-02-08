import re
import json
from django.utils import timezone
from django.conf import settings
from apps.core.services.bedrock import BedrockService


def _bedrock_enabled() -> bool:
    try:
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        return bool(SystemSettings.get_settings().bedrock_enabled)
    except Exception:
        return bool(getattr(settings, 'BEDROCK_ENABLED', False))


def _clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, value))


def calculate_rule_score(lead):
    score = 0
    reasons = []

    if lead.email:
        score += 15
        reasons.append("E-Mail vorhanden (+15)")
    if lead.phone:
        score += 10
        reasons.append("Telefon vorhanden (+10)")
    if lead.company:
        score += 15
        reasons.append("Firma vorhanden (+15)")

    if lead.source in {'referral', 'event'}:
        score += 15
        reasons.append("Starke Quelle (+15)")
    elif lead.source in {'email', 'phone'}:
        score += 8
        reasons.append("Direkter Kontakt (+8)")

    if lead.status == 'qualified':
        score += 25
        reasons.append("Qualifiziert (+25)")
    elif lead.status == 'contacted':
        score += 12
        reasons.append("Kontaktiert (+12)")
    elif lead.status == 'new':
        score += 5
        reasons.append("Neu (+5)")

    if lead.website if hasattr(lead, 'website') else False:
        score += 5
        reasons.append("Website vorhanden (+5)")

    return _clamp(score), "; ".join(reasons)


def _parse_score(text):
    match = re.search(r"\b(\d{1,3})\b", text or "")
    if not match:
        return None
    value = int(match.group(1))
    return _clamp(value)


def _parse_score_json(text):
    try:
        data = json.loads(text)
    except Exception:
        return None, None
    if not isinstance(data, dict):
        return None, None
    score = data.get("score")
    reason = data.get("reason")
    if isinstance(score, int):
        return _clamp(score), reason
    return None, reason


def calculate_ai_score(lead):
    if not _bedrock_enabled():
        return None, "Bedrock deaktiviert"
    try:
        prompt = (
            "Bewerte den Lead-Qualitaets-Score von 0 bis 100 und gib eine kurze Begründung.\n"
            "Gib JSON zurück: {\"score\": 0-100, \"reason\": \"...\"}\n"
            f"Name: {lead.name}\n"
            f"Firma: {lead.company}\n"
            f"Status: {lead.status}\n"
            f"Quelle: {lead.source}\n"
            f"E-Mail: {lead.email}\n"
            f"Telefon: {lead.phone}\n"
        )
        client = BedrockService()
        response = client.converse(prompt)
        score, reason = _parse_score_json(response)
        if score is None:
            score = _parse_score(response)
        if score is None:
            return None, "AI-Antwort unklar"
        return score, (reason or "AI-Score berechnet")
    except Exception as exc:
        return None, f"AI Fehler: {exc}"


def update_lead_score(lead, use_ai=True):
    rule_score, reasons = calculate_rule_score(lead)
    ai_score = 0
    if use_ai:
        ai_value, ai_reason = calculate_ai_score(lead)
        if ai_value is not None:
            ai_score = ai_value
            reasons = f"{reasons}; {ai_reason}" if reasons else ai_reason
        else:
            reasons = f"{reasons}; {ai_reason}" if reasons else ai_reason

    total = _clamp(int(round((rule_score * 0.7) + (ai_score * 0.3))))
    lead.rule_score = rule_score
    lead.ai_score = ai_score
    lead.score = total
    lead.score_reason = reasons
    lead.score_updated_at = timezone.now()
    lead.save(update_fields=['rule_score', 'ai_score', 'score', 'score_reason', 'score_updated_at'])
    return lead
