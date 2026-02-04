"""
Vereinheitlichter KI-Service mit Fallback-Mechanismus
Unterstützt: LLAMA3 (lokal), Claude (API), OpenAI (API)
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

# Import AI-Services
try:
    from .llama3_service import llama3_service
    LLAMA3_AVAILABLE = llama3_service.is_available()
except ImportError:
    LLAMA3_AVAILABLE = False
    logger.warning("LLAMA3-Service nicht verfügbar")

try:
    import anthropic
    CLAUDE_AVAILABLE = bool(getattr(settings, 'CLAUDE_API_KEY', None))
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = bool(getattr(settings, 'OPENAI_API_KEY', None))
except ImportError:
    OPENAI_AVAILABLE = False


class UnifiedAIService:
    """
    Vereinheitlichter KI-Service mit intelligenter Provider-Auswahl

    Priority-Reihenfolge:
    1. LLAMA3 (lokal, kostenlos, schnell)
    2. Claude (API, gute Qualität)
    3. OpenAI (API, Fallback)
    """

    def __init__(self):
        """Initialisiert den vereinheitlichten KI-Service"""
        self.preferred_provider = getattr(settings, 'AI_PREFERRED_PROVIDER', 'llama3')

        # Provider-Status
        self.providers = {
            'llama3': LLAMA3_AVAILABLE,
            'claude': CLAUDE_AVAILABLE,
            'openai': OPENAI_AVAILABLE
        }

        # Claude-Client
        if CLAUDE_AVAILABLE:
            self.claude_client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        else:
            self.claude_client = None

        # OpenAI-Client
        if OPENAI_AVAILABLE:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
        else:
            self.openai_client = None

        # Statistiken
        self.usage_stats = {
            'llama3': 0,
            'claude': 0,
            'openai': 0,
            'failures': 0
        }

        logger.info(f"Unified AI Service initialisiert - Provider: {self.providers}")

    def is_available(self) -> bool:
        """Prüft, ob mindestens ein KI-Provider verfügbar ist"""
        return any(self.providers.values())

    def get_available_providers(self) -> List[str]:
        """Gibt Liste verfügbarer Provider zurück"""
        return [provider for provider, available in self.providers.items() if available]

    def _get_provider_priority(self) -> List[str]:
        """
        Gibt Provider-Priorität basierend auf Präferenz zurück

        Returns:
            Liste von Providern in Prioritäts-Reihenfolge
        """
        providers = self.get_available_providers()

        # Bevorzugten Provider nach vorne
        if self.preferred_provider in providers:
            providers.remove(self.preferred_provider)
            providers.insert(0, self.preferred_provider)

        return providers

    def categorize_ticket(self, title: str, description: str) -> Tuple[Optional[str], Optional[float], str]:
        """
        Kategorisiert Ticket mit Fallback-Mechanismus

        Args:
            title: Ticket-Titel
            description: Ticket-Beschreibung

        Returns:
            Tuple (Kategorie, Konfidenz, Provider)
        """
        for provider in self._get_provider_priority():
            try:
                if provider == 'llama3':
                    category, confidence = llama3_service.categorize_ticket(title, description)
                    if category:
                        self.usage_stats['llama3'] += 1
                        logger.info(f"Ticket kategorisiert mit LLAMA3: {category}")
                        return category, confidence, 'llama3'

                elif provider == 'claude' and self.claude_client:
                    category, confidence = self._categorize_with_claude(title, description)
                    if category:
                        self.usage_stats['claude'] += 1
                        logger.info(f"Ticket kategorisiert mit Claude: {category}")
                        return category, confidence, 'claude'

                elif provider == 'openai' and self.openai_client:
                    category, confidence = self._categorize_with_openai(title, description)
                    if category:
                        self.usage_stats['openai'] += 1
                        logger.info(f"Ticket kategorisiert mit OpenAI: {category}")
                        return category, confidence, 'openai'

            except Exception as e:
                logger.error(f"Fehler bei {provider} Kategorisierung: {e}")
                continue

        self.usage_stats['failures'] += 1
        return None, None, 'none'

    def _categorize_with_claude(self, title: str, description: str) -> Tuple[Optional[str], Optional[float]]:
        """Kategorisiert mit Claude API"""
        prompt = f"""Kategorisiere dieses Helpdesk-Ticket in EINE der folgenden Kategorien:
Login & Authentifizierung, E-Mail & Kommunikation, Performance & Geschwindigkeit, Hardware-Probleme, Software & Installation, Netzwerk & Verbindung, Sicherheit & Zugriff, Datenbank & Speicher, Sonstiges

Titel: {title}
Beschreibung: {description}

Antworte NUR mit dem exakten Namen der Kategorie."""

        try:
            message = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            category = message.content[0].text.strip()
            return category, 0.9
        except Exception as e:
            logger.error(f"Claude API Fehler: {e}")
            return None, None

    def _categorize_with_openai(self, title: str, description: str) -> Tuple[Optional[str], Optional[float]]:
        """Kategorisiert mit OpenAI API"""
        prompt = f"""Kategorisiere dieses Helpdesk-Ticket in EINE der folgenden Kategorien:
Login & Authentifizierung, E-Mail & Kommunikation, Performance & Geschwindigkeit, Hardware-Probleme, Software & Installation, Netzwerk & Verbindung, Sicherheit & Zugriff, Datenbank & Speicher, Sonstiges

Titel: {title}
Beschreibung: {description}

Antworte NUR mit dem exakten Namen der Kategorie."""

        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            category = response.choices[0].message.content.strip()
            return category, 0.9
        except Exception as e:
            logger.error(f"OpenAI API Fehler: {e}")
            return None, None

    def suggest_priority(self, title: str, description: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Schlägt Ticket-Priorität vor mit Fallback

        Args:
            title: Ticket-Titel
            description: Ticket-Beschreibung

        Returns:
            Tuple (Priorität, Begründung, Provider)
        """
        for provider in self._get_provider_priority():
            try:
                if provider == 'llama3':
                    priority, reason = llama3_service.suggest_priority(title, description)
                    if priority:
                        self.usage_stats['llama3'] += 1
                        return priority, reason, 'llama3'

                elif provider == 'claude' and self.claude_client:
                    priority, reason = self._suggest_priority_claude(title, description)
                    if priority:
                        self.usage_stats['claude'] += 1
                        return priority, reason, 'claude'

                elif provider == 'openai' and self.openai_client:
                    priority, reason = self._suggest_priority_openai(title, description)
                    if priority:
                        self.usage_stats['openai'] += 1
                        return priority, reason, 'openai'

            except Exception as e:
                logger.error(f"Fehler bei {provider} Prioritäts-Vorschlag: {e}")
                continue

        return None, None, 'none'

    def _suggest_priority_claude(self, title: str, description: str) -> Tuple[Optional[str], Optional[str]]:
        """Priorität mit Claude"""
        prompt = f"""Bewerte die Dringlichkeit dieses Tickets:
Titel: {title}
Beschreibung: {description}

Wähle: critical, high, medium, low
Format: Priorität: [wert]
Begründung: [kurze Erklärung]"""

        try:
            message = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            response = message.content[0].text.strip()
            # Parse response
            lines = response.split('\n')
            priority = None
            reason = ""
            for line in lines:
                if 'priorität:' in line.lower():
                    priority = line.split(':', 1)[1].strip().lower()
                elif 'begründung:' in line.lower():
                    reason = line.split(':', 1)[1].strip()
            return priority, reason
        except Exception as e:
            logger.error(f"Claude Priority Error: {e}")
            return None, None

    def _suggest_priority_openai(self, title: str, description: str) -> Tuple[Optional[str], Optional[str]]:
        """Priorität mit OpenAI"""
        prompt = f"""Bewerte die Dringlichkeit dieses Tickets:
Titel: {title}
Beschreibung: {description}

Wähle: critical, high, medium, low
Format: Priorität: [wert]
Begründung: [kurze Erklärung]"""

        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2
            )
            text = response.choices[0].message.content.strip()
            # Parse response
            lines = text.split('\n')
            priority = None
            reason = ""
            for line in lines:
                if 'priorität:' in line.lower():
                    priority = line.split(':', 1)[1].strip().lower()
                elif 'begründung:' in line.lower():
                    reason = line.split(':', 1)[1].strip()
            return priority, reason
        except Exception as e:
            logger.error(f"OpenAI Priority Error: {e}")
            return None, None

    def generate_chat_response(self, message: str, context: List[Dict] = None) -> Tuple[Optional[str], str]:
        """
        Generiert Chat-Antwort mit Fallback

        Args:
            message: Benutzer-Nachricht
            context: Chat-Kontext

        Returns:
            Tuple (Antwort, Provider)
        """
        for provider in self._get_provider_priority():
            try:
                if provider == 'llama3':
                    response = llama3_service.generate_chat_response(message, context)
                    if response:
                        self.usage_stats['llama3'] += 1
                        return response, 'llama3'

                elif provider == 'claude' and self.claude_client:
                    response = self._chat_with_claude(message, context)
                    if response:
                        self.usage_stats['claude'] += 1
                        return response, 'claude'

                elif provider == 'openai' and self.openai_client:
                    response = self._chat_with_openai(message, context)
                    if response:
                        self.usage_stats['openai'] += 1
                        return response, 'openai'

            except Exception as e:
                logger.error(f"Fehler bei {provider} Chat-Response: {e}")
                continue

        return None, 'none'

    def _chat_with_claude(self, message: str, context: List[Dict] = None) -> Optional[str]:
        """Chat mit Claude API"""
        system_prompt = """Sie sind ein freundlicher Support-Agent. Antworten Sie auf Deutsch mit förmlicher Sie-Anrede,
kurz und präzise. Bei komplexen Problemen empfehlen Sie einen menschlichen Agent."""

        messages = []
        if context:
            for msg in context[-5:]:
                messages.append({
                    "role": "assistant" if not msg.get('is_from_visitor') else "user",
                    "content": msg.get('message', msg.get('content', ''))
                })
        messages.append({"role": "user", "content": message})

        try:
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=256,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude Chat Error: {e}")
            return None

    def _chat_with_openai(self, message: str, context: List[Dict] = None) -> Optional[str]:
        """Chat mit OpenAI API"""
        system_prompt = """Sie sind ein freundlicher Support-Agent. Antworten Sie auf Deutsch mit förmlicher Sie-Anrede,
kurz und präzise. Bei komplexen Problemen empfehlen Sie einen menschlichen Agent."""

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            for msg in context[-5:]:
                messages.append({
                    "role": "assistant" if not msg.get('is_from_visitor') else "user",
                    "content": msg.get('message', msg.get('content', ''))
                })
        messages.append({"role": "user", "content": message})

        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=512,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")
            return None

    def get_stats(self) -> Dict:
        """Gibt Nutzungsstatistiken zurück"""
        total_requests = sum(self.usage_stats.values())

        stats = {
            'total_requests': total_requests,
            'providers': self.providers,
            'usage': self.usage_stats,
            'preferred_provider': self.preferred_provider
        }

        if total_requests > 0:
            stats['distribution'] = {
                provider: round(count / total_requests * 100, 1)
                for provider, count in self.usage_stats.items()
                if count > 0
            }

        # LLAMA3-spezifische Stats
        if LLAMA3_AVAILABLE:
            stats['llama3_performance'] = llama3_service.get_performance_stats()

        return stats


# Globale Instanz
unified_ai_service = UnifiedAIService()
