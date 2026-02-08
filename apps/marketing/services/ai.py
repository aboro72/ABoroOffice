import json
from django.utils import timezone
from apps.core.services.bedrock import BedrockService


def _safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {}


class MarketingAIService:
    def __init__(self):
        self.client = BedrockService()

    def generate_content(self, asset_type: str, channel: str, brief: str) -> dict:
        prompt = (
            "Erstelle Marketing-Content basierend auf dem Briefing. "
            "Gib JSON zurück: {\"title\":\"...\",\"content\":\"...\",\"cta\":\"...\"}.\n"
            f"Typ: {asset_type}\n"
            f"Kanal: {channel}\n"
            f"Briefing: {brief}\n"
        )
        data = _safe_json(self.client.converse(prompt))
        if not data:
            content = self.client.converse(
                f"Schreibe einen Marketing-Entwurf. Typ: {asset_type}, Kanal: {channel}.\nBriefing: {brief}"
            )
            return {"title": "Entwurf", "content": content, "cta": ""}
        return data

    def generate_ideas(self, topic: str) -> list:
        prompt = (
            "Gib 5 Content-Ideen als JSON-Liste zurück, z.B. [\"Idee 1\", ...].\n"
            f"Thema: {topic}\n"
        )
        data = _safe_json(self.client.converse(prompt))
        if isinstance(data, list):
            return data
        text = self.client.converse(f"Nenne 5 Content-Ideen zum Thema: {topic}")
        return [line.strip('- ').strip() for line in text.splitlines() if line.strip()][:5]
