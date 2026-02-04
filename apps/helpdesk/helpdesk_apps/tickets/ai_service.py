"""
AI Service für automatische Ticket-Responses mit LLAMA3-Integration
"""
import anthropic
import logging
from django.conf import settings
from .models import Ticket, TicketComment
from apps.helpdesk.helpdesk_apps.knowledge.models import KnowledgeArticle
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings

logger = logging.getLogger(__name__)

# Import Unified AI Service für LLAMA3
try:
    from apps.helpdesk.helpdesk_apps.ai.unified_ai_service import unified_ai_service
    UNIFIED_AI_AVAILABLE = unified_ai_service.is_available()
except ImportError:
    UNIFIED_AI_AVAILABLE = False
    logger.warning("Unified AI Service nicht verfügbar - Fallback auf Claude-only")


class ClaudeAIService:
    """Service to interact with AI for auto-responses (Claude + LLAMA3)"""

    def __init__(self):
        self.client = None
        self.use_llama3 = getattr(settings, 'USE_LLAMA3', True) and UNIFIED_AI_AVAILABLE

        if hasattr(settings, 'CLAUDE_API_KEY') and settings.CLAUDE_API_KEY:
            self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

        logger.info(f"Ticket AI Service - LLAMA3: {self.use_llama3}, Claude: {bool(self.client)}")

    def is_available(self):
        """Check if AI is configured and available (Claude or LLAMA3)"""
        return self.client is not None or self.use_llama3

    def categorize_ticket_auto(self, ticket):
        """
        Automatische Ticket-Kategorisierung mit LLAMA3 (wenn verfügbar)

        Args:
            ticket: Ticket-Instanz

        Returns:
            Tuple (category, confidence, provider) oder (None, None, None)
        """
        if not self.use_llama3:
            return None, None, None

        try:
            logger.info(f"Auto-kategorisiere Ticket {ticket.ticket_number} mit LLAMA3")
            category, confidence, provider = unified_ai_service.categorize_ticket(
                ticket.title,
                ticket.description
            )

            if category and confidence and confidence > 0.7:
                logger.info(f"Ticket kategorisiert: {category} (Konfidenz: {confidence}, Provider: {provider})")
                return category, confidence, provider

        except Exception as e:
            logger.error(f"Fehler bei Auto-Kategorisierung: {e}")

        return None, None, None

    def suggest_ticket_priority_auto(self, ticket):
        """
        Automatische Prioritäts-Vorschlag mit LLAMA3

        Args:
            ticket: Ticket-Instanz

        Returns:
            Tuple (priority, reason, provider) oder (None, None, None)
        """
        if not self.use_llama3:
            return None, None, None

        try:
            logger.info(f"Priorität-Vorschlag für Ticket {ticket.ticket_number} mit LLAMA3")
            priority, reason, provider = unified_ai_service.suggest_priority(
                ticket.title,
                ticket.description
            )

            if priority:
                logger.info(f"Priorität vorgeschlagen: {priority} ({reason}) [Provider: {provider}]")
                return priority, reason, provider

        except Exception as e:
            logger.error(f"Fehler bei Prioritäts-Vorschlag: {e}")

        return None, None, None

    def get_relevant_knowledge(self, query, limit=3):
        """Search knowledge base for relevant articles"""
        from django.db.models import Q

        articles = KnowledgeArticle.objects.filter(
            status='published',
            is_public=True
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(keywords__icontains=query)
        )[:limit]

        return articles

    def _strip_existing_signature(self, text: str) -> str:
        """Remove common signature phrases from AI responses."""
        lines = text.rstrip().splitlines()
        signature_idx = None

        signature_markers = [
            "mit freundlichen grüßen",
            "freundliche grüße",
            "beste grüße",
            "herzliche grüße",
            "best regards",
            "regards,",
            "i.a.",
            "i. a.",
            "i.a ",
            "i. a ",
            "ab oro-soft support-agent",
            "avoro-soft support-agent",
            "aboro-soft helpdesk-system",
            "aboro-soft support-team",
        ]

        for idx, line in enumerate(lines):
            stripped = line.strip().lower()
            for marker in signature_markers:
                if marker in stripped:
                    signature_idx = idx
                    break
            if signature_idx is not None:
                break

        if signature_idx is not None:
            return "\n".join(lines[:signature_idx]).rstrip()
        return text.strip()

    def _remove_noise_lines(self, text: str, agent_name: str | None) -> str:
        """Strip helper tags/emojis the AI sometimes adds before we append our signature."""
        cleaned_lines = []
        agent_normalized = None
        if agent_name:
            agent_normalized = " ".join(agent_name.lower().split())

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append(line)
                continue

            normalized = " ".join(stripped.lower().split())
            if normalized.startswith("[agent]"):
                continue
            if normalized in {"😊", ":)", ":-)", "😃", "🤔💻"}:
                continue
            if "aboro-soft helpdesk-system" in normalized:
                continue
            if "aboro-soft support-agent" in normalized:
                continue
            if "aboro-soft support-team" in normalized:
                continue
            if agent_normalized and normalized == f"sie {agent_normalized}":
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _append_signature(self, response_text: str, agent=None) -> str:
        """Append the configured email signature to AI responses."""
        try:
            settings_obj = SystemSettings.get_settings()
            signature = (settings_obj.email_signature or "").strip()
            company_name = settings_obj.company_name or "Support-Team"
        except Exception:
            signature = ""
            company_name = "Support-Team"

        agent_name = None
        if agent is not None:
            if hasattr(agent, "full_name") and agent.full_name:
                agent_name = agent.full_name
            elif getattr(agent, "first_name", None) or getattr(agent, "last_name", None):
                agent_name = f"{agent.first_name} {agent.last_name}".strip()
            else:
                agent_name = getattr(agent, "username", None)

        signature_body = signature.strip() if signature else ""
        if agent_name and "{agent_name}" in signature_body:
            signature_body = signature_body.replace("{agent_name}", agent_name)

        body_lines = [line.strip() for line in signature_body.splitlines() if line.strip()]
        if not body_lines:
            body_lines = [company_name]

        final_lines = []
        greeting_line = "Mit freundlichen Grüßen,"
        if not any("mit freundlichen grüßen" in line.lower() for line in body_lines):
            final_lines.append(greeting_line)

        if agent_name:
            agent_line = f"i.A. {agent_name}"
            if not any(agent_name.lower() in line.lower() for line in body_lines):
                final_lines.append(agent_line)

        final_lines.extend(body_lines)

        # Remove unwanted lines, e.g., duplicated agent references or legacy branding.
        filtered_lines = []
        for line in final_lines:
            stripped = line.strip()
            lower = stripped.lower()
            if agent_name and lower == f"sie {agent_name.lower()}":
                continue
            if "[agent]" in lower:
                continue
            if "aboro-soft helpdesk-system" in lower:
                continue
            if "aboro-soft support-agent" in lower:
                continue
            if lower in {"😊", ":)", ":-)"}:
                continue
            filtered_lines.append(stripped)

        signature_text = "\n".join(filtered_lines).strip()

        response_text = self._remove_noise_lines(response_text, agent_name)
        response_text = self._strip_existing_signature(response_text)

        # Avoid double-appending if signature already present.
        if signature_text in response_text:
            return response_text
        return f"{response_text}\n\n{signature_text}"

    def suggest_ticket_response(self, ticket, agent=None):
        """
        Generiert einen AI-Antwortvorschlag für ein Ticket
        Der Agent kann den Vorschlag annehmen, bearbeiten oder ablehnen

        Args:
            ticket: Ticket-Instanz

        Returns:
            dict: {
                'text': 'Vorgeschlagene Antwort',
                'provider': 'llama3/claude/openai',
                'confidence': 0.0-1.0,
                'kb_articles': [KnowledgeArticle, ...],
                'success': True/False
            }
        """
        try:
            # Hole alle bisherigen Kommentare für Kontext
            comments_context = []
            for comment in ticket.comments.all().order_by('created_at'):
                role = 'customer' if comment.author.role == 'customer' else 'agent'
                comments_context.append({
                    'role': role,
                    'content': comment.content,
                    'author': comment.author.full_name
                })

            # Hole relevante KB-Artikel
            kb_articles = self.get_relevant_knowledge(
                f"{ticket.title} {ticket.description}",
                limit=3
            )

            kb_context = ""
            if kb_articles:
                kb_context = "\n\nRelevante Wissensdatenbank-Artikel:\n"
                for article in kb_articles:
                    kb_context += f"- {article.title}: {article.content[:300]}...\n"

            # Baue Prompt für AI
            prompt = f"""Du bist ein professioneller Support-Agent für das ABoro-Soft Helpdesk-System.

TICKET-INFORMATIONEN:
Nummer: {ticket.ticket_number}
Titel: {ticket.title}
Beschreibung: {ticket.description}
Priorität: {ticket.get_priority_display()}
Kategorie: {ticket.category.name if ticket.category else 'Keine'}
Erstellt von: {ticket.created_by.full_name}

BISHERIGE KOMMUNIKATION:
"""

            if comments_context:
                for comment in comments_context:
                    prompt += f"\n[{comment['role'].upper()}] {comment['author']}: {comment['content']}\n"
            else:
                prompt += "Noch keine Kommentare vorhanden.\n"

            prompt += kb_context

            prompt += f"""

AUFGABE:
Schreibe eine hilfreiche, professionelle Antwort für den Support-Agent, die dieser an den Kunden senden kann.

WICHTIG - ANREDE:
- Verwende IMMER die förmliche SIE-Form (Sie, Ihr, Ihnen)
- NIEMALS Du/Dich/Dir verwenden
- NIEMALS "können Sie" und "kannst du" mischen
- Konsequent förmlich bleiben

RICHTLINIEN:
- Schreibe auf Deutsch mit förmlicher Sie-Anrede
- Beginne mit "Sehr geehrte/r Frau/Herr {ticket.created_by.last_name}," oder "Guten Tag {ticket.created_by.first_name} {ticket.created_by.last_name},"
- Sei freundlich und professionell
- Gebe Sie konkrete Lösungsschritte, wenn möglich
- Nutzen Sie die Wissensdatenbank-Artikel als Referenz
- Halten Sie sich präzise (max. 250 Wörter)
- Enden Sie mit einer freundlichen Grußformel
- Erwähnen Sie, dass wir bei weiteren Fragen zur Verfügung stehen
- FÜGE KEINE Signatur oder Kontaktdaten an; dies übernimmt das System automatisch

Schreiben Sie NUR die Antwort, keine Metakommentare."""

            # Verwende Unified AI Service wenn verfügbar
            if self.use_llama3 and UNIFIED_AI_AVAILABLE:
                logger.info(f"Generiere AI-Antwortvorschlag für Ticket {ticket.ticket_number} mit Unified AI Service")

                # Konvertiere in das richtige Format für unified_ai_service
                response, provider = unified_ai_service.generate_chat_response(prompt, [])

                if response:
                    response = self._append_signature(response, agent=agent)
                    return {
                        'text': response,
                        'provider': provider,
                        'confidence': 0.8,
                        'kb_articles': list(kb_articles),
                        'success': True
                    }

            # Fallback zu Claude wenn verfügbar
            if self.client:
                logger.info(f"Generiere AI-Antwortvorschlag für Ticket {ticket.ticket_number} mit Claude")
                message = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = self._append_signature(message.content[0].text, agent=agent)

                return {
                    'text': response_text,
                    'provider': 'claude',
                    'confidence': 0.85,
                    'kb_articles': list(kb_articles),
                    'success': True
                }

            return {
                'text': None,
                'provider': None,
                'confidence': 0.0,
                'kb_articles': [],
                'success': False,
                'error': 'Kein AI-Provider verfügbar'
            }

        except Exception as e:
            logger.error(f"Fehler bei AI-Antwortvorschlag: {e}")
            return {
                'text': None,
                'provider': None,
                'confidence': 0.0,
                'kb_articles': [],
                'success': False,
                'error': str(e)
            }

    def should_auto_respond(self, ticket):
        """Determine if ticket should get auto-response"""
        # Only auto-respond to new tickets
        if ticket.status != 'open':
            return False

        # Don't auto-respond if already assigned
        if ticket.assigned_to:
            return False

        # Don't auto-respond if already has comments
        if ticket.comments.exists():
            return False

        # Only auto-respond to low/medium priority
        if ticket.priority in ['high', 'critical']:
            return False

        return True

    def generate_auto_response(self, ticket):
        """Generate an automatic response using Claude AI"""
        if not self.is_available():
            return None

        # Get relevant knowledge articles
        kb_articles = self.get_relevant_knowledge(ticket.title + ' ' + ticket.description)

        # Build context from knowledge base
        kb_context = ""
        if kb_articles:
            kb_context = "\n\nRelevante Wissensdatenbank-Artikel:\n"
            for article in kb_articles:
                kb_context += f"\n- {article.title}:\n{article.content[:500]}...\n"

        # Build prompt for Claude
        prompt = f"""Du bist ein hilfsbereiter Support-Agent für das ABoro-Soft Helpdesk-System.

Ein Kunde hat folgendes Ticket erstellt:

Titel: {ticket.title}
Beschreibung: {ticket.description}
Priorität: {ticket.get_priority_display()}
Kategorie: {ticket.category.name if ticket.category else 'Keine'}

{kb_context}

Aufgabe:
- Analysiere das Problem des Kunden
- Wenn das Problem einfach ist und du eine Lösung aus den Wissensdatenbank-Artikeln ableiten kannst, gib eine hilfreiche Antwort
- Wenn das Problem komplex ist oder keine passende Lösung in der Wissensdatenbank ist, sage dem Kunden freundlich, dass ein Support-Agent sich um sein Anliegen kümmern wird
- Schreibe auf Deutsch
- Sei freundlich und professionell
- Halte dich kurz (max. 200 Wörter)

Antworte NICHT mit einer Lösung wenn:
- Das Problem technisch komplex ist
- Es um sensible Daten geht
- Es um Abrechnungen oder Verträge geht
- Du dir nicht sicher bist

Beginne mit "Hallo {ticket.created_by.first_name}," und ende mit einer freundlichen Grußformel."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Determine if this is a helpful answer or a "wait for agent" message
            is_solution = any(word in response_text.lower() for word in [
                'lösung', 'können sie', 'versuchen sie', 'folgende schritte', 'hier ist'
            ])

            return {
                'text': response_text,
                'is_solution': is_solution,
                'kb_articles': list(kb_articles)
            }

        except Exception as e:
            print(f"Claude AI Error: {e}")
            return None

    def create_auto_comment(self, ticket):
        """Create an automatic comment on a ticket if appropriate"""
        if not self.should_auto_respond(ticket):
            return None

        response_data = self.generate_auto_response(ticket)

        if not response_data:
            return None

        # Create the comment
        comment = TicketComment.objects.create(
            ticket=ticket,
            author=ticket.created_by,  # System acts as customer
            content=response_data['text'] + "\n\n---\n🤖 Diese Antwort wurde automatisch von unserer KI generiert. Ein Support-Agent wird sich bei Bedarf zusätzlich um Ihr Anliegen kümmern.",
            is_internal=False
        )

        # If it's a potential solution, update ticket status
        if response_data['is_solution']:
            ticket.status = 'pending'  # Waiting for customer confirmation
            ticket.save()

        return comment


# Create a global instance
ai_service = ClaudeAIService()
