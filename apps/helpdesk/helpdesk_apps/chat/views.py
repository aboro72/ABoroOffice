from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_exempt
from django.template.loader import render_to_string
from django.http import HttpResponse
import json
import uuid
import time
import threading
from .models import ChatSession, ChatMessage, ChatSettings
from .enhanced_ai_service import get_ai_response_for_chat
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.helpdesk.helpdesk_apps.api.license_checker import LicenseFeatureChecker, require_feature

User = get_user_model()


def send_ai_response(session_id, message):
    """
    Send AI response after a delay (runs in background thread)
    """
    try:
        system_settings = SystemSettings.get_settings()
        
        # Wait for the configured delay (default to 2 seconds if not set)
        delay = getattr(system_settings, 'ai_response_delay', 2)
        time.sleep(delay)
        
        session = ChatSession.objects.get(session_id=session_id)
        
        # Send AI response if AI is enabled and no agent assigned
        if system_settings.ai_enabled and not session.assigned_agent:
            ai_response = get_ai_response_for_chat(message, session)
            
            if ai_response:
                # Create AI response message
                ChatMessage.objects.create(
                    session=session,
                    message=ai_response,
                    is_from_visitor=False,
                    sender_name="KI-Assistent",
                    message_type='text'
                )
                
                # Update session status to indicate AI is handling it
                if session.status != 'active':
                    session.status = 'active'
                    session.save()
                    
                    # Send system message about AI assistance only once
                    if not session.messages.filter(sender_name="System", message_type='system').exists():
                        ChatMessage.objects.create(
                            session=session,
                            message="🤖 Ein KI-Assistent steht Ihnen zur Verfügung. Bei komplexeren Problemen wird automatisch ein Support-Agent hinzugezogen.",
                            is_from_visitor=False,
                            sender_name="System",
                            message_type='system'
                        )
            else:
                # Fallback if AI doesn't respond
                ChatMessage.objects.create(
                    session=session,
                    message="🤖 Entschuldigung, ich habe momentan technische Probleme. Ein Support-Agent wurde benachrichtigt und wird Ihnen helfen.",
                    is_from_visitor=False,
                    sender_name="KI-Assistent",
                    message_type='text'
                )
    except Exception as e:
        # Log error but don't fail
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"AI response error: {e}")
        
        # Try to send error message to user
        try:
            session = ChatSession.objects.get(session_id=session_id)
            ChatMessage.objects.create(
                session=session,
                message="⚠️ Technisches Problem bei der KI-Antwort. Ein Support-Agent wurde benachrichtigt.",
                is_from_visitor=False,
                sender_name="System",
                message_type='system'
            )
        except:
            pass


def should_send_ai_response(session):
    """
    Determine if AI response should be sent
    """
    system_settings = SystemSettings.get_settings()
    
    # Initialize license checker
    if system_settings.license_code:
        LicenseFeatureChecker.set_license(system_settings.license_code)
    
    # Check if AI automation feature is available in license
    if not LicenseFeatureChecker.has_feature('ai_automation'):
        return False
    
    # Check if AI is enabled
    if not system_settings.ai_enabled:
        return False
    
    # Always send AI response if no agent is assigned (regardless of status)
    if not session.assigned_agent:
        return True
    
    # Don't send AI response if agent is already assigned
    return False


def should_escalate_to_agent(session):
    """
    Determine if chat should be escalated to human agent based on AI conversation analysis
    """
    # Count total messages in session
    total_messages = session.messages.count()
    user_messages = session.messages.filter(is_from_visitor=True).count()
    
    # Auto-escalate after 4 user messages without resolution
    if user_messages >= 4:
        return True
    
    # Check for escalation keywords in recent user messages
    escalation_keywords = [
        'frustriert', 'frustrated', 'hilft nicht', 'doesn\'t help', 'not working',
        'funktioniert nicht', 'agent', 'mitarbeiter', 'person', 'human',
        'sprechen', 'talk to', 'supervisor', 'manager', 'komplex', 'complex',
        'dringend', 'urgent', 'wichtig', 'important', 'sofort', 'immediately'
    ]
    
    recent_messages = session.messages.filter(
        is_from_visitor=True
    ).order_by('-timestamp')[:2]
    
    for msg in recent_messages:
        if any(keyword in msg.message.lower() for keyword in escalation_keywords):
            return True
    
    # Check if AI has provided multiple solutions without success indicators
    ai_messages = session.messages.filter(is_from_visitor=False, message_type='text').count()
    if ai_messages >= 3 and user_messages >= 3:
        return True
    
    return False


@xframe_options_exempt
def chat_widget(request):
    """Render the chat widget for embedding in websites"""
    settings = ChatSettings.get_settings()
    
    # Check if chat is available or AI is enabled
    from datetime import timedelta
    online_threshold = timezone.now() - timedelta(minutes=5)
    
    # Initialize license checker
    system_settings = SystemSettings.get_settings()
    if system_settings.license_code:
        LicenseFeatureChecker.set_license(system_settings.license_code)
    
    # Check license restrictions (nur für interne Nutzung, nicht für Widget-Embedding)
    embedded = request.GET.get('embedded', 'false').lower() == 'true'
    if not embedded and not LicenseFeatureChecker.has_feature('live_chat'):
        return render(request, 'chat/feature_restricted.html', {
            'feature': 'Live Chat',
            'required_license': 'Professional or higher'
        })
    
    # Check for available agents (simplified - just check if they're active)
    available_agents = User.objects.filter(
        role__in=['support_agent', 'admin'],
        is_active=True
    ).count()
    
    # For more accurate online detection, check last_activity if field exists
    try:
        available_agents_with_activity = User.objects.filter(
            role__in=['support_agent', 'admin'],
            is_active=True,
            last_activity__gte=online_threshold
        ).count()
        # Use the activity-based count if it's available
        available_agents = available_agents_with_activity
    except:
        # If last_activity field doesn't exist, assume no agents online for proper AI fallback
        available_agents = 0
    
    # Check AI availability (requires ai_automation license feature)
    ai_available = (system_settings.ai_enabled and 
                   LicenseFeatureChecker.has_feature('ai_automation'))
    
    # Check if loaded in iframe or as embedded widget
    is_iframe = request.GET.get('iframe', 'false').lower() == 'true' or \
               request.headers.get('Sec-Fetch-Dest') == 'iframe'
    is_embedded = request.GET.get('embedded', 'false').lower() == 'true'
    
    # Check if customer is logged in (from URL parameters)
    is_customer = request.GET.get('customer', 'false').lower() == 'true'
    user_name = request.GET.get('user_name', '')
    user_email = request.GET.get('user_email', '')
    
    context = {
        'settings': settings,
        'is_available': settings.is_enabled and (available_agents > 0 or ai_available),
        'available_agents': available_agents,
        'ai_available': ai_available,
        'session_id': str(uuid.uuid4()),
        'is_iframe': is_iframe,
        'is_embedded': is_embedded,
        'is_customer': is_customer,
        'user_name': user_name,
        'user_email': user_email,
    }
    
    response = render(request, 'chat/widget.html', context)
    
    # Zusätzlich sicherstellen, dass keine frame-blocking Headers gesetzt sind
    if 'X-Frame-Options' in response:
        del response['X-Frame-Options']
    
    # Setze explizit CSP für iframe-Einbettung
    origin = request.META.get('HTTP_ORIGIN', '')
    referer = request.META.get('HTTP_REFERER', '')
    
    if origin or referer:
        # Hole erlaubte Domains
        chat_settings = ChatSettings.get_settings()
        allowed_domains = [d.strip() for d in chat_settings.allowed_domains.split(',') if d.strip()]
        
        # Prüfe ob Request von erlaubter Domain kommt
        is_allowed = any(
            (origin and origin.startswith(allowed)) or 
            (referer and referer.startswith(allowed))
            for allowed in allowed_domains
        )
        
        if is_allowed:
            response['Content-Security-Policy'] = f"frame-ancestors 'self' {' '.join(allowed_domains)}"
        else:
            response['Content-Security-Policy'] = "frame-ancestors 'none'"
    
    return response


def widget_data(request):
    """Return widget data as JSON for direct embedding"""
    settings = ChatSettings.get_settings()
    
    # Check if chat is available or AI is enabled
    from datetime import timedelta
    online_threshold = timezone.now() - timedelta(minutes=5)
    
    # Check for available agents (simplified - just check if they're active)
    available_agents = User.objects.filter(
        role__in=['support_agent', 'admin'],
        is_active=True
    ).count()
    
    # For more accurate online detection, check last_activity if field exists
    try:
        available_agents_with_activity = User.objects.filter(
            role__in=['support_agent', 'admin'],
            is_active=True,
            last_activity__gte=online_threshold
        ).count()
        # Use the activity-based count if it's available
        available_agents = available_agents_with_activity
    except:
        # If last_activity field doesn't exist, assume no agents online for proper AI fallback
        available_agents = 0
    
    # Check AI availability
    system_settings = SystemSettings.get_settings()
    ai_available = system_settings.ai_enabled
    
    # Check if customer is logged in (from URL parameters)
    is_customer = request.GET.get('customer', 'false').lower() == 'true'
    user_name = request.GET.get('user_name', '')
    user_email = request.GET.get('user_email', '')
    
    widget_data = {
        'session_id': str(uuid.uuid4()),
        'available_agents': available_agents,
        'ai_available': ai_available,
        'is_available': settings.is_enabled and (available_agents > 0 or ai_available),
        'widget_color': settings.widget_color,
        'is_customer': is_customer,
        'user_name': user_name,
        'user_email': user_email,
        'welcome_message': settings.welcome_message,
        'offline_message': settings.offline_message,
    }
    
    return JsonResponse({
        'success': True,
        'widget_data': widget_data
    })


@csrf_exempt
@require_http_methods(["POST"])
def start_chat(request):
    """Start a new chat session"""
    try:
        # Robust JSON parsing; fallbacks if client sends no/invalid JSON
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

        ref = request.META.get('HTTP_REFERER') or ''
        session_id = data.get('session_id') or f"web_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        name = (data.get('name') or 'Website Besucher').strip()
        email = (data.get('email') or f"visitor@{request.get_host()}").strip()
        message = data.get('message', '').strip()
        page_url = data.get('page_url') or ref

        # Check if this is a real user message or just a generic "Chat started" message
        # Generic messages from widget: "Chat gestartet von https://..." or "Chat gestartet"
        is_generic_message = (
            message.startswith('Chat gestartet von ') or
            message == 'Chat gestartet' or
            not message  # Empty message
        )
        has_user_message = bool(message) and not is_generic_message

        # Use generic message if user didn't provide one
        if not message:
            message = f"Chat gestartet von {ref}" if ref else 'Chat gestartet'

        # Get visitor IP
        visitor_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if visitor_ip:
            visitor_ip = visitor_ip.split(',')[0]
        else:
            visitor_ip = request.META.get('REMOTE_ADDR')

        # Create chat session
        session = ChatSession.objects.create(
            session_id=session_id,
            visitor_name=name,
            visitor_email=email,
            visitor_ip=visitor_ip,
            initial_message=message,
            visitor_page_url=page_url,
            status='waiting'
        )

        # Create initial message
        ChatMessage.objects.create(
            session=session,
            message=message,
            is_from_visitor=True,
            sender_name=name,
            message_type='text'
        )

        # KI antwortet NUR wenn der Benutzer tatsächlich eine Frage gestellt hat (nicht bei generischen Chat-Start-Nachrichten)
        if has_user_message and should_send_ai_response(session):
            # Start AI response in background thread
            ai_thread = threading.Thread(
                target=send_ai_response,
                args=(session.session_id, message)
            )
            ai_thread.daemon = True
            ai_thread.start()
        
        return JsonResponse({
            'success': True,
            'session_id': session.session_id,
            'status': session.status,
            'assigned_agent': session.assigned_agent.full_name if session.assigned_agent else None
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Send a message in an existing chat session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message = data.get('message')
        
        session = get_object_or_404(ChatSession, session_id=session_id)
        
        # Create message
        ChatMessage.objects.create(
            session=session,
            message=message,
            is_from_visitor=True,
            sender_name=session.visitor_name,
            message_type='text'
        )
        
        # Check if AI should respond
        if should_send_ai_response(session):
            # Check for auto-escalation before AI response
            if should_escalate_to_agent(session):
                # Create escalation message
                ChatMessage.objects.create(
                    session=session,
                    message="🚀 **Automatische Weiterleitung an Support-Agent**\n\nIch erkenne, dass Ihr Problem komplexere Unterstützung benötigt. Ein erfahrener Support-Agent wurde benachrichtigt und übernimmt in Kürze.\n\n✅ Alle bisherigen Informationen wurden übertragen\n✅ Prioritäre Bearbeitung\n✅ Direkter menschlicher Kontakt",
                    is_from_visitor=False,
                    sender_name="KI-Assistent",
                    message_type='system'
                )
                
                # Notify available agents (this could trigger email/push notifications)
                # For now, we'll just update the session status to indicate escalation needed
                session.status = 'escalated'
                session.save()
            else:
                # Start AI response in background thread
                ai_thread = threading.Thread(
                    target=send_ai_response,
                    args=(session_id, message)
                )
                ai_thread.daemon = True
                ai_thread.start()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_http_methods(["GET"])
def get_messages(request, session_id):
    """Get messages for a chat session"""
    try:
        session = get_object_or_404(ChatSession, session_id=session_id)
        messages = session.messages.all()
        
        message_data = []
        for msg in messages:
            message_data.append({
                'id': msg.id,
                'message': msg.message,
                'timestamp': msg.timestamp.isoformat(),
                'is_from_visitor': msg.is_from_visitor,
                'sender_name': msg.sender_name,
                'message_type': msg.message_type
            })
        
        return JsonResponse({
            'success': True,
            'messages': message_data,
            'session_status': session.status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def agent_dashboard(request):
    """Dashboard for agents to manage chats"""
    if request.user.role not in ['support_agent', 'admin']:
        return render(request, 'chat/access_denied.html')
    
    # Get active and waiting chats
    waiting_chats = ChatSession.objects.filter(status='waiting')
    escalated_chats = ChatSession.objects.filter(status='escalated')
    active_chats = ChatSession.objects.filter(
        status='active',
        assigned_agent=request.user
    )
    
    # Get AI-handled chats (active but no assigned agent)
    ai_handled_chats = ChatSession.objects.filter(
        status='active',
        assigned_agent__isnull=True
    )
    
    context = {
        'waiting_chats': waiting_chats,
        'escalated_chats': escalated_chats,
        'active_chats': active_chats,
        'ai_handled_chats': ai_handled_chats,
    }
    
    return render(request, 'chat/agent_dashboard.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def agent_take_chat(request, session_id):
    """Agent takes a waiting chat or takes over from AI"""
    if request.user.role not in ['support_agent', 'admin']:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        # Allow taking over from waiting, escalated, and AI-handled active chats
        session = get_object_or_404(
            ChatSession, 
            session_id=session_id, 
            status__in=['waiting', 'active', 'escalated']
        )
        
        # Check if chat is AI-handled (active but no assigned agent) or escalated
        is_ai_takeover = session.status == 'active' and not session.assigned_agent
        is_escalated = session.status == 'escalated'
        
        session.assigned_agent = request.user
        session.status = 'active'
        session.save()
        
        # Send appropriate system message
        if is_escalated:
            message_text = f"🚀 {request.user.full_name} hat Ihren eskalierten Chat übernommen und steht Ihnen jetzt persönlich zur Verfügung."
        elif is_ai_takeover:
            message_text = f"👨‍💻 {request.user.full_name} hat den Chat vom KI-Assistenten übernommen."
        else:
            message_text = f"👋 {request.user.full_name} hat den Chat übernommen."
            
        ChatMessage.objects.create(
            session=session,
            message=message_text,
            is_from_visitor=False,
            sender_name="System",
            message_type='system'
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def agent_send_message(request, session_id):
    """Agent sends a message"""
    if request.user.role not in ['support_agent', 'admin']:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        data = json.loads(request.body)
        message = data.get('message')
        
        session = get_object_or_404(
            ChatSession, 
            session_id=session_id, 
            assigned_agent=request.user
        )
        
        # Create message
        ChatMessage.objects.create(
            session=session,
            message=message,
            is_from_visitor=False,
            sender_name=request.user.full_name,
            agent=request.user,
            message_type='text'
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def end_chat(request, session_id):
    """End a chat session"""
    if request.user.role not in ['support_agent', 'admin']:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        session = get_object_or_404(
            ChatSession, 
            session_id=session_id, 
            assigned_agent=request.user
        )
        
        session.status = 'ended'
        session.ended_at = timezone.now()
        session.save()
        
        # Send system message
        ChatMessage.objects.create(
            session=session,
            message="Chat wurde beendet.",
            is_from_visitor=False,
            sender_name="System",
            message_type='system'
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def chat_detail(request, session_id):
    """Detailed view of a chat session for agents"""
    if request.user.role not in ['support_agent', 'admin']:
        return render(request, 'chat/access_denied.html')
    
    session = get_object_or_404(ChatSession, session_id=session_id)
    messages = session.messages.all()
    
    context = {
        'session': session,
        'messages': messages,
        'can_respond': session.assigned_agent == request.user and session.status == 'active'
    }
    
    return render(request, 'chat/chat_detail.html', context)


@login_required
def dashboard_stats(request):
    """Get dashboard statistics for agents (AJAX endpoint)"""
    if request.user.role not in ['support_agent', 'admin']:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        # Get chat counts
        waiting_chats = ChatSession.objects.filter(status='waiting').count()
        escalated_chats = ChatSession.objects.filter(status='escalated').count()
        active_chats = ChatSession.objects.filter(
            status='active',
            assigned_agent=request.user
        ).count()
        
        # Get AI-handled chats (active but no assigned agent)
        ai_handled_chats = ChatSession.objects.filter(
            status='active',
            assigned_agent__isnull=True
        ).count()
        
        # Get today's handled chats
        today_handled = ChatSession.objects.filter(
            status='ended',
            ended_at__date=timezone.now().date(),
            assigned_agent=request.user
        ).count()
        
        return JsonResponse({
            'success': True,
            'waiting_chats': waiting_chats,
            'escalated_chats': escalated_chats,
            'active_chats': active_chats,
            'ai_handled_chats': ai_handled_chats,
            'today_handled': today_handled,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def widget_script(request):
    """
    Serve the external chat widget JavaScript for embedding
    """
    settings = ChatSettings.get_settings()
    system_settings = SystemSettings.get_settings()
    
    # Widget configuration
    widget_config = {
        'chatHost': request.build_absolute_uri('/').rstrip('/'),
        'widgetColor': settings.widget_color,
        'position': settings.widget_position,
        'autoOpen': False,
        'language': 'de'
    }
    
    # Read the widget script template
    import os
    from django.conf import settings as django_settings
    
    script_path = os.path.join(django_settings.BASE_DIR, 'templates', 'chat', 'pure_widget.js')
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
    except FileNotFoundError:
        # Fallback inline script
        script_content = """
        console.error('Aboro Chat Widget: Script file not found');
        window.AboroChat = {
            open: () => console.warn('Chat widget not available'),
            close: () => {},
            toggle: () => {},
            destroy: () => {}
        };
        """
    
    # Inject configuration
    config_js = f"window.AboroChatConfig = {json.dumps(widget_config)};"
    script_content = config_js + "\n\n" + script_content
    
    response = HttpResponse(script_content, content_type='application/javascript; charset=utf-8')
    
    # Firefox-freundliche CORS-Header
    origin = request.META.get('HTTP_ORIGIN', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    is_firefox = 'Firefox' in user_agent
    
    if origin or is_firefox:
        response['Access-Control-Allow-Origin'] = origin if origin else '*'
        response['Access-Control-Allow-Credentials'] = 'false' if is_firefox else 'true'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Accept, Content-Type, X-Requested-With'
        
        if is_firefox:
            response['Vary'] = 'Origin'
    
    # Cache headers (reduziert für Firefox)
    if is_firefox:
        response['Cache-Control'] = 'public, max-age=300'  # 5 Minuten für Firefox
    else:
        response['Cache-Control'] = 'public, max-age=3600'  # 1 Stunde für andere Browser
    
    return response


def debug_widget_script(request):
    """
    Serve the debug chat widget JavaScript for troubleshooting
    """
    settings = ChatSettings.get_settings()
    system_settings = SystemSettings.get_settings()
    
    # Widget configuration
    widget_config = {
        'chatHost': request.build_absolute_uri('/').rstrip('/'),
        'widgetColor': settings.widget_color,
        'position': settings.widget_position,
        'autoOpen': False,
        'language': 'de'
    }
    
    # Read the debug widget script
    import os
    from django.conf import settings as django_settings
    
    script_path = os.path.join(django_settings.BASE_DIR, 'templates', 'chat', 'debug_widget.js')
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
    except FileNotFoundError:
        # Fallback inline script
        script_content = """
        console.error('Aboro Debug Widget: Script file not found');
        alert('Debug widget script not found!');
        """
    
    # Inject configuration
    config_js = f"window.AboroChatConfig = {json.dumps(widget_config)};"
    script_content = config_js + "\n\n" + script_content
    
    response = HttpResponse(script_content, content_type='application/javascript; charset=utf-8')
    
    # Firefox-freundliche CORS-Header
    origin = request.META.get('HTTP_ORIGIN', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    is_firefox = 'Firefox' in user_agent
    
    if origin or is_firefox:
        response['Access-Control-Allow-Origin'] = origin if origin else '*'
        response['Access-Control-Allow-Credentials'] = 'false' if is_firefox else 'true'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Accept, Content-Type, X-Requested-With'
        
        if is_firefox:
            response['Vary'] = 'Origin'
    
    # No cache for debug script
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


def widget_test(request):
    """
    Test page for the external chat widget
    """
    settings = ChatSettings.get_settings()
    
    # Parse allowed domains
    allowed_domains = [d.strip() for d in settings.allowed_domains.split(',') if d.strip()]
    
    context = {
        'chat_settings': settings,
        'allowed_domains': allowed_domains
    }
    
    return render(request, 'chat/external_widget.html', context)
