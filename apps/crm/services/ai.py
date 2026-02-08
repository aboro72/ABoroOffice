import json
from django.conf import settings
from django.utils import timezone
from apps.core.services.bedrock import BedrockService


def _bedrock_enabled() -> bool:
    try:
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        return bool(SystemSettings.get_settings().bedrock_enabled)
    except Exception:
        return bool(getattr(settings, 'BEDROCK_ENABLED', False))


def _safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {}


class CrmAIService:
    def __init__(self):
        if not _bedrock_enabled():
            raise RuntimeError("Bedrock not enabled")
        self.client = BedrockService()

    def summarize_account(self, account, recent_notes=None) -> str:
        notes = recent_notes or []
        prompt = (
            "Erstelle eine kurze CRM-Zusammenfassung (3-6 Sätze) für folgendes Konto.\n"
            f"Name: {account.name}\n"
            f"Branche: {account.industry}\n"
            f"Website: {account.website}\n"
            f"Status: {account.status}\n"
            f"Kontakte: {account.contacts.count()}\n"
            f"Opportunities: {account.opportunities.count()}\n"
            f"Notizen: {', '.join(n.content[:80] for n in notes)}\n"
        )
        return self.client.converse(prompt)

    def summarize_lead(self, lead, recent_notes=None) -> str:
        notes = recent_notes or []
        prompt = (
            "Fasse den Lead kurz zusammen (3-5 Sätze) und gib eine Einschätzung zur nächsten Aktion.\n"
            f"Name: {lead.name}\n"
            f"Firma: {lead.company}\n"
            f"Status: {lead.status}\n"
            f"Quelle: {lead.source}\n"
            f"Score (gesamt): {lead.score}\n"
            f"Score (Regel): {lead.rule_score}\n"
            f"Score (AI): {lead.ai_score}\n"
            f"Notizen: {', '.join(n.content[:80] for n in notes)}\n"
        )
        return self.client.converse(prompt)

    def summarize_lead_with_next_steps(self, lead, recent_notes=None) -> dict:
        notes = recent_notes or []
        prompt = (
            "Erstelle eine kurze CRM-Zusammenfassung und konkrete nächste Schritte.\n"
            "Gib JSON zurück: {\"summary\":\"...\",\"next_steps\":[\"...\",\"...\"]}\n"
            f"Name: {lead.name}\n"
            f"Firma: {lead.company}\n"
            f"Status: {lead.status}\n"
            f"Quelle: {lead.source}\n"
            f"E-Mail: {lead.email}\n"
            f"Telefon: {lead.phone}\n"
            f"Website: {lead.website}\n"
            f"Notizen: {', '.join(n.content[:120] for n in notes)}\n"
        )
        data = _safe_json(self.client.converse(prompt))
        summary = data.get("summary", "") if isinstance(data, dict) else ""
        next_steps = data.get("next_steps", []) if isinstance(data, dict) else []
        if not summary:
            summary = self.client.converse(
                "Fasse den Lead kurz zusammen (3-5 Sätze).\n"
                f"Name: {lead.name}\n"
                f"Firma: {lead.company}\n"
                f"Status: {lead.status}\n"
                f"Quelle: {lead.source}\n"
            )
        if not next_steps:
            next_steps = [
                "Kontakt aufnehmen und Bedarf klären",
                "Termin für Erstgespräch vorschlagen",
            ]
        return {"summary": summary, "next_steps": next_steps}

    def draft_lead_followup_email(self, lead, recent_notes=None) -> dict:
        notes = recent_notes or []
        prompt = (
            "Schreibe eine professionelle Follow-up E-Mail (deutsch) für diesen Lead.\n"
            "Gib JSON zurück: {\"subject\":\"...\",\"body\":\"...\"}\n"
            f"Name: {lead.name}\n"
            f"Firma: {lead.company}\n"
            f"Status: {lead.status}\n"
            f"Notizen: {', '.join(n.content[:120] for n in notes)}\n"
        )
        data = _safe_json(self.client.converse(prompt))
        subject = data.get("subject", "") if isinstance(data, dict) else ""
        body = data.get("body", "") if isinstance(data, dict) else ""
        if not subject or not body:
            fallback = self.client.converse(
                "Schreibe eine kurze Follow-up E-Mail (deutsch) als Entwurf.\n"
                f"Name: {lead.name}\n"
                f"Firma: {lead.company}\n"
                f"Status: {lead.status}\n"
            )
            subject = subject or f"Kurzes Follow-up zu {lead.company or lead.name}"
            body = body or fallback
        return {"subject": subject, "body": body}

    def answer_lead_question(self, lead, question: str, recent_notes=None) -> str:
        notes = recent_notes or []
        prompt = (
            "Beantworte die Frage anhand der CRM-Daten. Falls etwas fehlt, sag es klar.\n"
            f"Frage: {question}\n"
            f"Name: {lead.name}\n"
            f"Firma: {lead.company}\n"
            f"E-Mail: {lead.email}\n"
            f"Telefon: {lead.phone}\n"
            f"Website: {lead.website}\n"
            f"Status: {lead.status}\n"
            f"Notizen: {', '.join(n.content[:160] for n in notes)}\n"
        )
        return self.client.converse(prompt)

    def draft_opportunity_email(self, opportunity, contact=None) -> str:
        contact_name = contact and contact.first_name or "Kundin/Kunde"
        prompt = (
            "Schreibe einen kurzen professionellen E-Mail-Entwurf (deutsch) "
            "für ein Follow-up zur Opportunity.\n"
            f"Kontakt: {contact_name}\n"
            f"Opportunity: {opportunity.name}\n"
            f"Phase: {opportunity.stage}\n"
            f"Betrag: {opportunity.amount}\n"
            "Ziel: Nächste Schritte vorschlagen und Termin anbieten.\n"
        )
        return self.client.converse(prompt)
