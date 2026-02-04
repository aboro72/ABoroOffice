"""
Enhanced AI Service für Support Chat
====================================

Erweiterte KI-Integration mit:
- FAQ-basierte Antworten
- Automatische Ticket-Erstellung
- Intelligente Eskalation
- Workflow: KI -> Agent -> Ticket
"""
import json
import logging
import re
from typing import Optional, Dict, List, Tuple
from django.db.models import Q
from django.utils import timezone
from helpdesk_apps.admin_panel.models import SystemSettings
from helpdesk_apps.knowledge.models import KnowledgeArticle
from helpdesk_apps.api.license_checker import LicenseFeatureChecker

logger = logging.getLogger(__name__)


class EnhancedAIService:
    """Enhanced AI Service mit FAQ-Integration und Ticket-Management"""
    
    def __init__(self):
        self.system_settings = SystemSettings.get_settings()
        
        # Initialize license checker
        if self.system_settings.license_code:
            LicenseFeatureChecker.set_license(self.system_settings.license_code)
    
    def is_ai_available(self) -> bool:
        """Prüfe ob KI verfügbar ist (Settings + Lizenz)"""
        if not self.system_settings.ai_enabled:
            return False
        
        # Prüfe Lizenz für AI Automation
        return LicenseFeatureChecker.has_feature('ai_automation')
    
    def get_ai_response_for_chat(self, message: str, session, chat_history: List = None) -> Optional[str]:
        """
        Hauptfunktion für KI-Antworten mit FAQ-Integration
        
        Workflow:
        1. FAQ-Suche nach relevanten Artikeln
        2. KI generiert Antwort basierend auf FAQ + Nachricht
        3. Bei komplexen Anfragen -> Eskalation empfehlen
        4. Bei wiederholten Problemen -> Ticket erstellen
        """
        if not self.is_ai_available():
            return None
        
        try:
            # 1. FAQ-Artikel suchen
            relevant_faqs = self._search_relevant_faqs(message)
            
            # 2. Chat-Kontext analysieren
            context = self._analyze_chat_context(session, chat_history)
            
            # 3. Entscheidung: FAQ-Antwort, Eskalation oder Ticket?
            if context['should_create_ticket']:
                return self._handle_ticket_creation(session, message, context)
            elif context['should_escalate']:
                return self._handle_escalation(session, message, relevant_faqs)
            else:
                return self._generate_faq_response(message, relevant_faqs, context)
                
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return self._get_fallback_response()
    
    def _search_relevant_faqs(self, message: str) -> List[KnowledgeArticle]:
        """Suche relevante FAQ-Artikel basierend auf der Nachricht"""
        try:
            # Nur öffentliche und veröffentlichte Artikel
            base_query = KnowledgeArticle.objects.filter(
                is_public=True,
                status='published'
            )

            # Keywords aus der Nachricht extrahieren
            keywords = self._extract_keywords(message)

            if not keywords:
                return []

            # Suche nach relevanten Artikeln
            query = Q()
            for keyword in keywords:
                query |= (
                    Q(title__icontains=keyword) |
                    Q(content__icontains=keyword) |
                    Q(keywords__icontains=keyword)
                )

            relevant_articles = base_query.filter(query).distinct()[:5]

            logger.info(f"Found {len(relevant_articles)} relevant FAQ articles for: {keywords}")
            return list(relevant_articles)

        except Exception as e:
            logger.error(f"FAQ search error: {e}")
            return []
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extrahiere relevante Keywords aus der Nachricht"""
        # Bereinige die Nachricht
        message = message.lower().strip()

        # Entferne Stoppwörter und extrahiere wichtige Begriffe
        stopwords = {
            'ich', 'bin', 'habe', 'kann', 'nicht', 'ist', 'das', 'der', 'die', 'und',
            'oder', 'aber', 'mit', 'von', 'zu', 'im', 'am', 'ein', 'eine', 'einen',
            'wie', 'was', 'wo', 'wann', 'warum', 'bitte', 'danke', 'hello', 'hi',
            'the', 'and', 'or', 'but', 'with', 'from', 'to', 'in', 'at', 'a', 'an'
        }

        # Wörter und Nummern extrahieren (z.B. "413", "fehler", etc.)
        # Regex: Buchstaben (auch Umlaute) oder Nummern, mindestens 2 Zeichen
        words = re.findall(r'\b[a-zäöüß0-9]{2,}\b', message)

        # Stoppwörter entfernen
        keywords = [word for word in words if word not in stopwords]

        # Begrenzen auf die ersten 10 wichtigsten Keywords
        return keywords[:10]
    
    def _analyze_chat_context(self, session, chat_history: List = None) -> Dict:
        """Analysiere den Chat-Kontext für Entscheidungen"""
        context = {
            'message_count': session.messages.filter(is_from_visitor=True).count(),
            'session_duration': (timezone.now() - session.created_at).total_seconds() / 60,
            'ai_responses_count': session.messages.filter(
                is_from_visitor=False,
                sender_name="KI-Assistent"
            ).count(),
            'should_escalate': False,
            'should_create_ticket': False,
            'escalation_reason': None
        }
        
        # Entscheidungslogik
        if context['message_count'] >= 5:
            context['should_escalate'] = True
            context['escalation_reason'] = "Mehr als 4 Nachrichten ohne Lösung"
        
        if context['session_duration'] > 15:  # 15 Minuten
            context['should_escalate'] = True
            context['escalation_reason'] = "Lange Chat-Dauer"
        
        if context['ai_responses_count'] >= 4:
            context['should_create_ticket'] = True
            context['escalation_reason'] = "Mehrfache KI-Antworten ohne Erfolg"
        
        # Prüfe auf Eskalations-Keywords
        if chat_history:
            last_message = chat_history[-1] if chat_history else ""
            escalation_keywords = [
                'agent', 'mitarbeiter', 'person', 'human', 'mensch',
                'hilft nicht', 'funktioniert nicht', 'frustrated', 'problem'
            ]
            
            if any(keyword in last_message.lower() for keyword in escalation_keywords):
                context['should_escalate'] = True
                context['escalation_reason'] = "Kunde möchte mit Mitarbeiter sprechen"
        
        return context
    
    def _generate_faq_response(self, message: str, faqs: List, context: Dict) -> str:
        """Generiere Antwort basierend auf FAQ-Artikeln"""
        if not faqs:
            return self._get_general_response(message)
        
        # Verwende den ersten/besten FAQ-Artikel
        best_faq = faqs[0]
        
        # Vereinfache und personalisiere die FAQ-Antwort
        simplified_content = self._simplify_faq_content(best_faq.content)
        
        response = f"Gerne helfe ich Ihnen weiter!\\n\\n{simplified_content}"
        
        # Füge zusätzliche Hilfe hinzu, falls weitere FAQs verfügbar sind
        if len(faqs) > 1:
            response += "\\n\\nWeitere hilfreiche Artikel:\\n"
            for faq in faqs[1:3]:  # Maximal 2 weitere
                response += f"• {faq.title}\\n"
        
        response += "\\n\\nKann ich Ihnen noch bei etwas anderem helfen?"
        
        return response
    
    def _simplify_faq_content(self, content: str) -> str:
        """Vereinfache FAQ-Inhalt für Chat-Antworten"""
        import html

        # Entferne HTML-Tags falls vorhanden
        content = re.sub(r'<[^>]+>', '', content)

        # Dekodiere HTML-Entities (z.B. &auml; -> ä, &nbsp; -> Leerzeichen)
        content = html.unescape(content)

        # Begrenzen auf ersten Absatz oder ersten 300 Zeichen
        paragraphs = content.split('\n\n')
        simplified = paragraphs[0]

        if len(simplified) > 300:
            simplified = simplified[:300] + "..."

        return simplified.strip()
    
    def _get_general_response(self, message: str) -> str:
        """Allgemeine Antwort wenn keine FAQ gefunden wurde"""
        greetings = ['hallo', 'hi', 'hello', 'guten tag', 'hey']
        thanks = ['danke', 'thanks', 'vielen dank']
        
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in greetings):
            return ("Hallo! Ich bin der KI-Assistent und helfe Ihnen gerne weiter. "
                   "Beschreiben Sie mir bitte Ihr Anliegen, dann kann ich Ihnen passende "
                   "Informationen aus unserer Wissensdatenbank bereitstellen.")
        
        if any(thank in message_lower for thank in thanks):
            return ("Gerne geschehen! Falls Sie noch weitere Fragen haben, bin ich hier. "
                   "Einen schönen Tag noch!")
        
        # Standard-Antwort
        return ("Vielen Dank für Ihre Nachricht. Ich durchsuche gerade unsere "
               "Wissensdatenbank nach passenden Informationen. Leider konnte ich "
               "zu Ihrer spezifischen Frage keine direkten Artikel finden. "
               "Ein Support-Mitarbeiter wird sich gleich um Ihr Anliegen kümmern.")
    
    def _handle_escalation(self, session, message: str, faqs: List) -> str:
        """Eskalation an menschlichen Agent"""
        # Session auf 'waiting' setzen für Agent-Übernahme
        session.status = 'waiting'
        session.save()
        
        response = ("Ich leite Sie jetzt an einen unserer Support-Mitarbeiter weiter, "
                   "der Ihnen persönlich helfen kann. ")
        
        if faqs:
            response += ("Hier sind noch einige Artikel aus unserer Wissensdatenbank, "
                        "die möglicherweise relevant sind:\\n\\n")
            for faq in faqs[:2]:
                response += f"• {faq.title}\\n"
        
        response += ("\\nEin Mitarbeiter wird sich gleich bei Ihnen melden. "
                    "Bitte haben Sie einen Moment Geduld.")
        
        return response
    
    def _handle_ticket_creation(self, session, message: str, context: Dict) -> str:
        """Erstelle automatisch ein Ticket"""
        try:
            # Ticket erstellen
            ticket_number = self._create_ticket_from_session(session, message, context)
            
            if ticket_number:
                response = (f"Ich habe für Sie ein Support-Ticket erstellt (#{ticket_number}). "
                           f"Ein Mitarbeiter wird sich in Kürze um Ihr Anliegen kümmern. "
                           f"Sie erhalten eine E-Mail-Bestätigung mit allen Details.")
                
                # Session schließen, da Ticket erstellt wurde
                session.status = 'ended'
                session.ended_at = timezone.now()
                session.save()
                
                return response
            else:
                # Fallback: Eskalation an Agent
                return self._handle_escalation(session, message, [])
                
        except Exception as e:
            logger.error(f"Ticket creation error: {e}")
            return self._handle_escalation(session, message, [])
    
    def _create_ticket_from_session(self, session, latest_message: str, context: Dict) -> Optional[str]:
        """Erstelle Ticket aus Chat-Session"""
        try:
            from helpdesk_apps.tickets.models import Ticket, Category
            
            # Chat-Inhalt zusammenstellen
            messages = session.messages.filter(
                message_type='text'
            ).order_by('timestamp')
            
            chat_content = []
            for msg in messages:
                sender = "Kunde" if msg.is_from_visitor else "KI-Assistent"
                chat_content.append(
                    f"[{msg.timestamp.strftime('%H:%M')}] {sender}: {msg.message}"
                )
            
            chat_summary = "\\n".join(chat_content)
            
            # Kategorie bestimmen
            category = self._determine_ticket_category(latest_message, session)
            
            # Ticket erstellen
            ticket = Ticket.objects.create(
                title=f"Chat Support: {latest_message[:50]}...",
                description=(
                    f"Automatisch erstelltes Ticket aus Chat-Session\\n\\n"
                    f"Grund: {context.get('escalation_reason', 'Mehrfache KI-Versuche')}\\n"
                    f"Session ID: {session.session_id}\\n"
                    f"Dauer: {context.get('session_duration', 0):.1f} Minuten\\n\\n"
                    f"Chat-Verlauf:\\n{chat_summary}"
                ),
                customer_email=session.visitor_email or 'unbekannt@chat.local',
                customer_name=session.visitor_name or 'Chat-Besucher',
                category=category,
                priority='medium',
                status='open',
                created_from_chat=True
            )
            
            logger.info(f"Created ticket {ticket.ticket_number} from chat session {session.session_id}")
            return ticket.ticket_number
            
        except Exception as e:
            logger.error(f"Error creating ticket from session: {e}")
            return None
    
    def _determine_ticket_category(self, message: str, session) -> 'Category':
        """Bestimme Ticket-Kategorie basierend auf Chat-Inhalt"""
        from helpdesk_apps.tickets.models import Category
        
        # Versuche Kategorie basierend auf Keywords zu bestimmen
        message_lower = message.lower()
        
        category_keywords = {
            'technischer support': ['fehler', 'error', 'bug', 'funktioniert nicht', 'problem'],
            'allgemeine anfrage': ['frage', 'information', 'wie', 'was', 'hilfe'],
            'rechnungswesen': ['rechnung', 'zahlung', 'payment', 'billing', 'invoice'],
        }
        
        for category_name, keywords in category_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Auto-kategorisiert: {category_name}'}
                )
                return category
        
        # Standard-Kategorie
        category, created = Category.objects.get_or_create(
            name="Chat Support",
            defaults={'description': 'Tickets aus Chat-Sessions'}
        )
        return category
    
    def _get_fallback_response(self) -> str:
        """Fallback-Antwort bei Fehlern"""
        return ("Entschuldigung, ich habe gerade technische Schwierigkeiten. "
               "Ein Support-Mitarbeiter wird sich gleich um Ihr Anliegen kümmern.")


def get_ai_response_for_chat(message: str, session, chat_history: List = None) -> Optional[str]:
    """
    Hauptfunktion für KI-Chat-Antworten (für Kompatibilität)
    
    Args:
        message: Nachricht des Benutzers
        session: Chat-Session Objekt
        chat_history: Bisheriger Chat-Verlauf (optional)
        
    Returns:
        KI-Antwort oder None
    """
    ai_service = EnhancedAIService()
    return ai_service.get_ai_response_for_chat(message, session, chat_history)
