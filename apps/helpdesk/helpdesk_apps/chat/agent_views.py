"""
Support Agent Chat Dashboard Views
Für Agents und Administratoren zum Verwalten von Chat-Sessions
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q, Count, Max, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
import json

from .models import ChatSession, ChatMessage, ChatSettings
from apps.helpdesk.helpdesk_apps.tickets.models import Ticket
from apps.helpdesk.helpdesk_apps.knowledge.models import KnowledgeArticle
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from .ai_service import get_ai_response_for_chat

User = get_user_model()


def is_support_staff(user):
    """Prüfe ob User Support-Staff ist"""
    return user.is_authenticated and (
        user.is_superuser or 
        user.role in ['admin', 'support_agent']
    )


@login_required
@user_passes_test(is_support_staff)
def chat_dashboard(request):
    """
    Haupt-Dashboard für Support Agents
    Zeigt alle aktiven Chat-Sessions, wartende Kunden, etc.
    """
    # Aktive Sessions (wartend oder in Bearbeitung)
    waiting_sessions = ChatSession.objects.filter(
        status='waiting'
    ).order_by('created_at')
    
    active_sessions = (
        ChatSession.objects.filter(
            status='active',
            assigned_agent__isnull=False
        )
        .annotate(last_activity=Coalesce(Max('messages__timestamp'), F('created_at')))
        .order_by('-last_activity')
    )
    
    # Meine Sessions (für den aktuellen Agent)
    my_sessions = (
        ChatSession.objects.filter(
            assigned_agent=request.user,
            status='active'
        )
        .annotate(last_activity=Coalesce(Max('messages__timestamp'), F('created_at')))
        .order_by('-last_activity')
    )
    
    # Statistiken
    today = timezone.now().date()
    stats = {
        'waiting_count': waiting_sessions.count(),
        'active_count': active_sessions.count(),
        'my_sessions_count': my_sessions.count(),
        'today_sessions': ChatSession.objects.filter(created_at__date=today).count(),
        'today_closed': ChatSession.objects.filter(
            status='ended',
            ended_at__date=today
        ).count(),
    }
    
    # AI-Only Sessions (von KI bearbeitet, aber noch kein Agent)
    ai_sessions = (
        ChatSession.objects.filter(
            status='active',
            assigned_agent__isnull=True
        )
        .annotate(
            message_count=Count('messages'),
            last_activity=Coalesce(Max('messages__timestamp'), F('created_at')),
        )
        .filter(message_count__gte=1)
        .order_by('-last_activity')
    )
    
    context = {
        'waiting_sessions': waiting_sessions,
        'active_sessions': active_sessions,
        'my_sessions': my_sessions,
        'ai_sessions': ai_sessions,
        'stats': stats,
    }
    
    return render(request, 'chat/agent_dashboard.html', context)


@login_required
@user_passes_test(is_support_staff)
def chat_session_detail(request, session_id):
    """
    Detailansicht einer Chat-Session für Agents
    Hier können Agents chatten und die Session verwalten
    """
    session = get_object_or_404(ChatSession, session_id=session_id)
    
    # Nachrichten laden (chronologisch)
    messages = session.messages.all().order_by('timestamp')
    
    # Prüfe ob Session bereits einem anderen Agent zugewiesen ist
    if session.assigned_agent and session.assigned_agent != request.user:
        messages.warning(request, f'Diese Session ist bereits {session.assigned_agent.get_full_name()} zugewiesen.')
    
    # FAQ-Artikel für Quick-Antworten
    faq_articles = KnowledgeArticle.objects.filter(
        is_public=True,
        category__isnull=False
    ).order_by('category__name', 'title')[:10]
    
    context = {
        'session': session,
        'messages': messages,
        'faq_articles': faq_articles,
        'can_assign': session.assigned_agent is None or session.assigned_agent == request.user,
    }
    
    return render(request, 'chat/agent_chat_detail.html', context)


@csrf_exempt
@login_required
@user_passes_test(is_support_staff)
def take_chat_session(request, session_id):
    """Agent übernimmt eine Chat-Session"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    session = get_object_or_404(ChatSession, session_id=session_id)
    
    # Prüfe ob Session verfügbar ist
    if session.assigned_agent and session.assigned_agent != request.user:
        return JsonResponse({
            'error': f'Session bereits von {session.assigned_agent.get_full_name()} übernommen'
        }, status=400)
    
    # Session zuweisen
    session.assigned_agent = request.user
    session.status = 'active'
    session.save()
    
    # Systemnotiz an Kunde senden
    ChatMessage.objects.create(
        session=session,
        message=f"{request.user.get_full_name()} hat den Chat übernommen und wird Ihnen gleich antworten.",
        is_from_visitor=False,
        sender_name="System",
        message_type='system'
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Chat-Session übernommen',
        'agent_name': request.user.get_full_name()
    })


@csrf_exempt
@login_required
@user_passes_test(is_support_staff)
def send_agent_message(request, session_id):
    """Agent sendet Nachricht an Kunden"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    session = get_object_or_404(ChatSession, session_id=session_id)
    
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'error': 'Nachricht ist leer'}, status=400)
        
        # Prüfe Berechtigung
        if session.assigned_agent != request.user:
            return JsonResponse({'error': 'Nicht autorisiert'}, status=403)
        
        # Nachricht erstellen
        message = ChatMessage.objects.create(
            session=session,
            message=message_text,
            is_from_visitor=False,
            sender_name=request.user.get_full_name(),
            message_type='text'
        )
        
        # Session als aktiv markieren
        session.status = 'active'
        session.save()
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat(),
            'sender': message.sender_name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ungültiges JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@user_passes_test(is_support_staff)
def close_chat_session(request, session_id):
    """Chat-Session schließen"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    session = get_object_or_404(ChatSession, session_id=session_id)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'Von Agent geschlossen')
        create_ticket = data.get('create_ticket', False)
        
        # Prüfe Berechtigung
        if session.assigned_agent != request.user and not request.user.is_superuser:
            return JsonResponse({'error': 'Nicht autorisiert'}, status=403)
        
        # Abschlussnachricht senden
        ChatMessage.objects.create(
            session=session,
            message=f"Chat wurde beendet. Grund: {reason}",
            is_from_visitor=False,
            sender_name="System",
            message_type='system'
        )
        
        # Session schließen
        session.status = 'ended'
        session.ended_at = timezone.now()
        session.save()
        
        ticket_number = None
        
        # Optional: Ticket erstellen
        if create_ticket:
            ticket_number = create_ticket_from_chat(session, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Chat-Session geschlossen',
            'ticket_number': ticket_number
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ungültiges JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def create_ticket_from_chat(session, created_by):
    """Erstelle Ticket aus Chat-Session"""
    from apps.helpdesk.helpdesk_apps.tickets.models import Ticket, Category
    
    # Chat-Nachrichten zusammenfassen
    messages = session.messages.filter(
        message_type='text'
    ).order_by('timestamp')
    
    chat_content = []
    for msg in messages:
        sender = "Kunde" if msg.is_from_visitor else msg.sender_name
        chat_content.append(f"[{msg.timestamp.strftime('%H:%M')}] {sender}: {msg.message}")
    
    chat_summary = "\n".join(chat_content)
    
    # Standard-Kategorie finden oder erstellen
    category, created = Category.objects.get_or_create(
        name="Chat Support",
        defaults={'description': 'Tickets aus Chat-Sessions'}
    )
    
    # Ticket erstellen
    ticket = Ticket.objects.create(
        title=f"Chat Support - {session.visitor_name or 'Unbekannter Besucher'}",
        description=f"Ticket erstellt aus Chat-Session {session.session_id}\n\n"
                   f"Chat-Verlauf:\n{chat_summary}",
        customer_email=session.visitor_email or 'unbekannt@chat.local',
        customer_name=session.visitor_name or 'Unbekannter Besucher',
        category=category,
        priority='medium',
        status='open',
        assigned_to=created_by,
        created_from_chat=True
    )
    
    return ticket.ticket_number


@csrf_exempt  
@login_required
@user_passes_test(is_support_staff)
def transfer_to_ai(request, session_id):
    """Chat-Session zurück an KI übertragen"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    session = get_object_or_404(ChatSession, session_id=session_id)
    
    # Prüfe ob KI verfügbar ist
    system_settings = SystemSettings.get_settings()
    if not system_settings.ai_enabled:
        return JsonResponse({'error': 'KI ist nicht aktiviert'}, status=400)
    
    # Session von Agent entfernen
    session.assigned_agent = None
    session.save()
    
    # Nachricht an Kunde
    ChatMessage.objects.create(
        session=session,
        message="Sie werden nun wieder von unserem KI-Assistenten betreut. Ein Agent kann jederzeit eingreifen.",
        is_from_visitor=False,
        sender_name="System",
        message_type='system'
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Session an KI übertragen'
    })


@login_required
@user_passes_test(is_support_staff)
def get_session_messages(request, session_id):
    """Aktuelle Nachrichten einer Session laden (für Auto-Refresh)"""
    session = get_object_or_404(ChatSession, session_id=session_id)
    
    # Neueste Nachrichten seit letztem Check
    since = request.GET.get('since')
    if since:
        try:
            since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            messages = session.messages.filter(timestamp__gt=since_dt)
        except ValueError:
            messages = session.messages.all()
    else:
        messages = session.messages.all()
    
    messages = messages.order_by('timestamp')
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'message': msg.message,
            'is_from_visitor': msg.is_from_visitor,
            'sender_name': msg.sender_name,
            'message_type': msg.message_type,
            'timestamp': msg.timestamp.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'session_status': session.status,
        'assigned_agent': session.assigned_agent.get_full_name() if session.assigned_agent else None
    })


@csrf_exempt
@login_required
@user_passes_test(is_support_staff)
def use_faq_template(request, session_id):
    """FAQ-Artikel als Vorlage für Antwort verwenden"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        article_id = data.get('article_id')
        
        article = get_object_or_404(KnowledgeArticle, id=article_id)
        
        # Template-Text für Agent-Antwort vorbereiten
        template_text = f"Hier ist eine Antwort aus unserer Wissensdatenbank:\n\n{article.content}"
        
        return JsonResponse({
            'success': True,
            'template': template_text,
            'article_title': article.title
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ungültiges JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
