"""
LLAMA3 Local AI Service für Jetson Orin NX
Bietet lokale KI-Funktionen ohne Cloud-API-Abhängigkeit
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama nicht installiert. LLAMA3-Funktionen sind deaktiviert.")


class LLAMA3Service:
    """Service für lokale LLAMA3-KI auf Jetson Orin NX"""

    # Modell-Konfiguration
    DEFAULT_MODEL = "llama3.2-uncensored-3b"  # Kompakteres Standardmodell für lokale Bereitstellung
    FALLBACK_MODEL = "llama3.2-uncensored-3b"  # Sicherstellen, dass Fallback verfügbar ist

    # Performance-Einstellungen
    DEFAULT_TEMPERATURE = 0.3  # Niedrig für konsistente, schnelle Antworten
    MAX_TOKENS = 256  # Reduziert für Speicher-Optimierung

    # Kategorie-Mapping
    TICKET_CATEGORIES = [
        "Login & Authentifizierung",
        "E-Mail & Kommunikation",
        "Performance & Geschwindigkeit",
        "Hardware-Probleme",
        "Software & Installation",
        "Netzwerk & Verbindung",
        "Sicherheit & Zugriff",
        "Datenbank & Speicher",
        "Sonstiges"
    ]

    def __init__(self):
        """Initialisiert den LLAMA3-Service"""
        self.model = getattr(settings, 'LLAMA3_MODEL', self.DEFAULT_MODEL)
        self.available = OLLAMA_AVAILABLE and self._check_ollama_service()
        self.performance_metrics = []

        if self.available:
            logger.info(f"LLAMA3-Service initialisiert mit Modell: {self.model}")
        else:
            logger.warning("LLAMA3-Service nicht verfügbar")

    def _check_ollama_service(self) -> bool:
        """Prüft, ob Ollama-Service läuft"""
        if not OLLAMA_AVAILABLE:
            return False

        try:
            # Teste mit einfacher Anfrage
            ollama.list()
            return True
        except Exception as e:
            logger.error(f"Ollama-Service nicht erreichbar: {e}")
            return False

    def is_available(self) -> bool:
        """Prüft, ob LLAMA3-Service verfügbar ist"""
        return self.available

    def _chat(self, messages: List[Dict[str, str]], temperature: float = None) -> Optional[str]:
        """
        Interne Methode für Chat mit LLAMA3

        Args:
            messages: Liste von Nachrichten mit 'role' und 'content'
            temperature: Temperatur für Antwort-Generierung

        Returns:
            Antwort-Text oder None bei Fehler
        """
        if not self.available:
            return None

        temp = temperature if temperature is not None else self.DEFAULT_TEMPERATURE

        try:
            start_time = time.time()

            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': temp,
                    'num_predict': self.MAX_TOKENS,
                }
            )

            duration = time.time() - start_time

            # Performance-Metriken speichern
            self.performance_metrics.append({
                'timestamp': time.time(),
                'duration': duration,
                'model': self.model,
                'tokens': len(response['message']['content'].split())
            })

            # Nur letzte 100 Metriken behalten
            if len(self.performance_metrics) > 100:
                self.performance_metrics = self.performance_metrics[-100:]

            logger.info(f"LLAMA3-Antwort in {duration:.2f}s generiert")

            return response['message']['content'].strip()

        except Exception as e:
            logger.error(f"LLAMA3-Chat-Fehler: {e}")

            # Fallback auf kleineres Modell
            if self.model != self.FALLBACK_MODEL:
                logger.info(f"Fallback zu {self.FALLBACK_MODEL}")
                old_model = self.model
                self.model = self.FALLBACK_MODEL
                result = self._chat(messages, temperature)
                self.model = old_model  # Zurücksetzen
                return result

            return None

    def categorize_ticket(self, title: str, description: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Kategorisiert ein Ticket automatisch mit LLAMA3

        Args:
            title: Ticket-Titel
            description: Ticket-Beschreibung

        Returns:
            Tuple (Kategorie, Konfidenz) oder (None, None) bei Fehler
        """
        if not self.available:
            return None, None

        # Prompt für Kategorisierung
        system_prompt = f"""Du bist ein Experte für Helpdesk-Ticket-Kategorisierung.

Kategorisiere das folgende Ticket in GENAU EINE der folgenden Kategorien:
{', '.join(self.TICKET_CATEGORIES)}

Analysiere Titel und Beschreibung sorgfältig und wähle die am besten passende Kategorie.

WICHTIG: Antworte NUR mit dem exakten Namen der Kategorie, ohne zusätzlichen Text."""

        user_prompt = f"""Titel: {title}

Beschreibung: {description}

Kategorie:"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        response = self._chat(messages, temperature=0.1)  # Sehr niedrig für konsistente Kategorisierung

        if not response:
            return None, None

        # Extrahiere Kategorie aus Antwort
        category = response.strip()

        # Fuzzy-Matching falls nicht exakt
        if category not in self.TICKET_CATEGORIES:
            category = self._fuzzy_match_category(category)

        # Konfidenz berechnen (vereinfacht, basierend auf Antwortlänge)
        confidence = 0.9 if len(response.split()) <= 5 else 0.7

        logger.info(f"Ticket kategorisiert: '{category}' (Konfidenz: {confidence})")

        return category, confidence

    def _fuzzy_match_category(self, text: str) -> Optional[str]:
        """
        Findet beste Übereinstimmung für Kategorie

        Args:
            text: Kategorietext aus KI-Antwort

        Returns:
            Beste passende Kategorie oder None
        """
        text_lower = text.lower()

        # Keyword-Mapping
        keyword_map = {
            'login': 'Login & Authentifizierung',
            'passwort': 'Login & Authentifizierung',
            'anmelden': 'Login & Authentifizierung',
            'email': 'E-Mail & Kommunikation',
            'mail': 'E-Mail & Kommunikation',
            'langsam': 'Performance & Geschwindigkeit',
            'performance': 'Performance & Geschwindigkeit',
            'geschwindigkeit': 'Performance & Geschwindigkeit',
            'hardware': 'Hardware-Probleme',
            'drucker': 'Hardware-Probleme',
            'monitor': 'Hardware-Probleme',
            'software': 'Software & Installation',
            'installation': 'Software & Installation',
            'programm': 'Software & Installation',
            'netzwerk': 'Netzwerk & Verbindung',
            'internet': 'Netzwerk & Verbindung',
            'verbindung': 'Netzwerk & Verbindung',
            'sicherheit': 'Sicherheit & Zugriff',
            'zugriff': 'Sicherheit & Zugriff',
            'datenbank': 'Datenbank & Speicher',
            'speicher': 'Datenbank & Speicher',
        }

        for keyword, category in keyword_map.items():
            if keyword in text_lower:
                return category

        # Fallback: Exakte Teilstring-Suche
        for category in self.TICKET_CATEGORIES:
            if category.lower() in text_lower or text_lower in category.lower():
                return category

        # Default-Kategorie
        return "Sonstiges"

    def suggest_priority(self, title: str, description: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Schlägt Priorität für Ticket vor

        Args:
            title: Ticket-Titel
            description: Ticket-Beschreibung

        Returns:
            Tuple (Priorität, Begründung) oder (None, None)
        """
        if not self.available:
            return None, None

        system_prompt = """Du bist ein Helpdesk-Experte für Prioritäts-Bewertung.

Bewerte die Dringlichkeit des Tickets und wähle eine Priorität:
- critical: System komplett ausgefallen, viele Benutzer betroffen, Datenverlust-Gefahr
- high: Wichtige Funktion nicht verfügbar, mehrere Benutzer betroffen
- medium: Einzelner Benutzer, beeinträchtigt Arbeit, Workaround möglich
- low: Kosmetisches Problem, Feature-Request, keine dringende Notwendigkeit

Format der Antwort:
Priorität: [critical/high/medium/low]
Begründung: [Kurze Erklärung in 1-2 Sätzen]"""

        user_prompt = f"""Titel: {title}

Beschreibung: {description}"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        response = self._chat(messages, temperature=0.2)

        if not response:
            return None, None

        # Parse Antwort
        lines = response.split('\n')
        priority = None
        reason = ""

        for line in lines:
            if 'priorität:' in line.lower():
                priority_text = line.split(':', 1)[1].strip().lower()
                if 'critical' in priority_text or 'kritisch' in priority_text:
                    priority = 'critical'
                elif 'high' in priority_text or 'hoch' in priority_text:
                    priority = 'high'
                elif 'medium' in priority_text or 'mittel' in priority_text:
                    priority = 'medium'
                elif 'low' in priority_text or 'niedrig' in priority_text:
                    priority = 'low'
            elif 'begründung:' in line.lower():
                reason = line.split(':', 1)[1].strip()

        logger.info(f"Priorität vorgeschlagen: {priority} - {reason}")

        return priority, reason

    def generate_chat_response(self, message: str, context: List[Dict[str, str]] = None) -> Optional[str]:
        """
        Generiert Chat-Antwort mit LLAMA3

        Args:
            message: Benutzer-Nachricht
            context: Optional vorherige Nachrichten für Kontext

        Returns:
            KI-Antwort oder None
        """
        if not self.available:
            return None

        system_prompt = """Sie sind ein freundlicher Support-Agent.

RICHTLINIEN:
- Antworten auf DEUTSCH mit SIE-Anrede ("Sie", "Ihr", "Ihnen")
- Freundlich und professionell
- Kurze, klare Antworten (max. 100 Wörter)
- Bei komplexen Problemen: "Ein Support-Agent wird sich darum kümmern."

Beginnen Sie mit einer freundlichen Begrüßung."""

        messages = [{'role': 'system', 'content': system_prompt}]

        # Kontext hinzufügen
        if context:
            messages.extend(context[-5:])  # Letzte 5 Nachrichten

        messages.append({'role': 'user', 'content': message})

        response = self._chat(messages, temperature=0.7)  # Höher für natürlichere Antworten

        if response:
            logger.info(f"Chat-Antwort generiert: {len(response)} Zeichen")

        return response

    def analyze_ticket_sentiment(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Analysiert Stimmung/Dringlichkeit eines Tickets

        Args:
            text: Ticket-Text

        Returns:
            Tuple (Sentiment, Score) - Sentiment: positive/neutral/negative/urgent
        """
        if not self.available:
            return None, None

        system_prompt = """Analysiere die Stimmung und Dringlichkeit des folgenden Textes.

Bewerte als:
- positive: Freundlich, Frage ohne Frustration
- neutral: Sachlich, normale Anfrage
- negative: Frustration, Unzufriedenheit erkennbar
- urgent: Sehr dringend, kritisches Problem, Frustration

Antworte NUR mit: [Sentiment] [Score 0-10]
Beispiel: negative 7"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': text}
        ]

        response = self._chat(messages, temperature=0.1)

        if not response:
            return None, None

        # Parse Antwort
        parts = response.strip().split()
        sentiment = parts[0] if parts else None
        score = float(parts[1]) / 10.0 if len(parts) > 1 else 0.5

        return sentiment, score

    def get_performance_stats(self) -> Dict:
        """
        Gibt Performance-Statistiken zurück

        Returns:
            Dictionary mit Performance-Metriken
        """
        if not self.performance_metrics:
            return {
                'available': self.available,
                'total_requests': 0,
                'avg_response_time': 0,
                'model': self.model
            }

        avg_duration = sum(m['duration'] for m in self.performance_metrics) / len(self.performance_metrics)
        avg_tokens = sum(m['tokens'] for m in self.performance_metrics) / len(self.performance_metrics)

        return {
            'available': self.available,
            'model': self.model,
            'total_requests': len(self.performance_metrics),
            'avg_response_time': round(avg_duration, 2),
            'avg_tokens': round(avg_tokens, 1),
            'last_request': self.performance_metrics[-1]['timestamp'] if self.performance_metrics else None
        }


# Globale Instanz
llama3_service = LLAMA3Service()
