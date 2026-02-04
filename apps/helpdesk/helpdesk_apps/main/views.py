from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.utils.timezone import now as timezone_now
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from apps.helpdesk.helpdesk_apps.api.license_checker import LicenseFeatureChecker, require_feature

User = get_user_model()


@login_required
def dashboard(request):
    """Main dashboard view with license checking"""
    # Initialize license checker with current license
    from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
    settings_obj = SystemSettings.get_settings()
    if settings_obj.license_code:
        LicenseFeatureChecker.set_license(settings_obj.license_code)
    
    # Get license restrictions
    license_restrictions = LicenseFeatureChecker.get_feature_restrictions()
    
    context = {
        'stats': request.user.get_dashboard_stats() if hasattr(request.user, 'get_dashboard_stats') else {},
        'license_restrictions': license_restrictions,
        'max_agents': LicenseFeatureChecker.get_max_agents(),
    }
    return render(request, 'dashboard/index.html', context)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard class-based view"""
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = self.request.user.get_dashboard_stats() if hasattr(self.request.user, 'get_dashboard_stats') else {}
        
        # Add license information
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        settings_obj = SystemSettings.get_settings()
        if settings_obj.license_code:
            LicenseFeatureChecker.set_license(settings_obj.license_code)
        
        context['license_restrictions'] = LicenseFeatureChecker.get_feature_restrictions()
        context['max_agents'] = LicenseFeatureChecker.get_max_agents()
        
        return context


@login_required
def admin_settings(request):
    """Admin settings view - combines System Settings and Chat Settings"""
    
    # Check if user is admin
    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin')):
        return HttpResponseForbidden('Sie haben keine Berechtigung, diese Seite zu sehen.')
    
    from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
    from apps.helpdesk.helpdesk_apps.chat.models import ChatSettings
    from apps.helpdesk.helpdesk_apps.main.forms import AdminSettingsForm
    
    # Get or create settings objects
    system_settings = SystemSettings.get_settings()
    chat_settings = ChatSettings.get_settings()
    
    if request.method == 'POST':
        form = AdminSettingsForm(request.POST, request.FILES, 
                                system_settings=system_settings, 
                                chat_settings=chat_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Einstellungen wurden erfolgreich gespeichert!')
            return redirect('main:admin_settings')
    else:
        form = AdminSettingsForm(system_settings=system_settings, chat_settings=chat_settings)
    
    # Generate chat widget embed code
    # Use site_url from database if available, otherwise use Django settings
    site_url = system_settings.site_url if system_settings.site_url else getattr(settings, 'SITE_URL', 'http://localhost:8000')
    prefix = getattr(settings, 'HELPDESK_URL_PREFIX', '')
    widget_url = f"{site_url}{prefix}/chat/widget/"
    
    # Standard iFrame Code (kann in einigen Browsern blockiert werden)
    embed_code = f'''<!-- Aboro-IT Helpdesk Live Chat Widget (iFrame) -->
<iframe src="{widget_url}" 
        width="400" 
        height="600" 
        frameborder="0" 
        allow="microphone; camera; autoplay; encrypted-media"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-top-navigation"
        style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
</iframe>'''

    # Firefox-kompatible JavaScript Version
    js_embed_code = f'''<!-- Aboro-IT Helpdesk Live Chat Widget (Firefox-kompatibel) -->
<script>
(function() {{
    // Chat Widget Container
    var chatContainer = document.createElement('div');
    chatContainer.id = 'aboro-chat-widget';
    chatContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; width: 400px; height: 600px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); background: white; display: none; flex-direction: column; overflow: hidden;';
    
    // Chat Button
    var chatButton = document.createElement('div');
    chatButton.id = 'aboro-chat-button';
    chatButton.innerHTML = '💬';
    chatButton.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 10000; width: 60px; height: 60px; background: #667eea; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); transition: all 0.3s ease;';
    
    // Chat Header
    var chatHeader = document.createElement('div');
    chatHeader.style.cssText = 'background: #667eea; color: white; padding: 15px; font-weight: 600; text-align: center; font-family: Arial, sans-serif;';
    chatHeader.innerHTML = 'Live Chat Support';
    
    // Close Button
    var closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.style.cssText = 'position: absolute; top: 10px; right: 15px; background: none; border: none; color: white; font-size: 20px; cursor: pointer; width: 30px; height: 30px; border-radius: 50%; hover: rgba(255,255,255,0.2);';
    chatHeader.appendChild(closeButton);
    
    // Chat Content (iFrame als Fallback)
    var chatContent = document.createElement('div');
    chatContent.style.cssText = 'flex: 1; position: relative;';
    
    var iframe = document.createElement('iframe');
    iframe.src = '{widget_url}?embedded=true';
    iframe.style.cssText = 'width: 100%; height: 100%; border: none;';
    iframe.allow = 'microphone; camera; autoplay; encrypted-media';
    iframe.sandbox = 'allow-scripts allow-same-origin allow-forms allow-popups';
    
    chatContent.appendChild(iframe);
    chatContainer.appendChild(chatHeader);
    chatContainer.appendChild(chatContent);
    
    // Event Handlers
    chatButton.addEventListener('click', function() {{
        chatContainer.style.display = 'flex';
        chatButton.style.display = 'none';
    }});
    
    closeButton.addEventListener('click', function() {{
        chatContainer.style.display = 'none';
        chatButton.style.display = 'flex';
    }});
    
    // Button Hover Effects
    chatButton.addEventListener('mouseenter', function() {{
        this.style.transform = 'scale(1.1)';
        this.style.background = '#5a67d8';
    }});
    
    chatButton.addEventListener('mouseleave', function() {{
        this.style.transform = 'scale(1)';
        this.style.background = '#667eea';
    }});
    
    // Add to page
    document.body.appendChild(chatButton);
    document.body.appendChild(chatContainer);
    
    // Auto-open on page load (optional)
    // setTimeout(function() {{ chatButton.click(); }}, 2000);
}})();
</script>'''

    # Native JavaScript Version (ohne iFrame - für maximale Kompatibilität)
    native_js_code = f'''<!-- Aboro-IT Helpdesk Live Chat Widget (Native JavaScript - Maximale Kompatibilität) -->
<script>
(function() {{
    var CHAT_API_BASE = '{site_url}{prefix}/chat/api';
    var currentSessionId = null;
    var messages = [];
    var messageCheckInterval = null;
    
    // CSS Styles
    var styles = `
        .aboro-chat-widget * {{ box-sizing: border-box; }}
        .aboro-chat-button {{ 
            position: fixed; bottom: 20px; right: 20px; z-index: 10000; 
            width: 60px; height: 60px; background: #667eea; border-radius: 50%; 
            cursor: pointer; display: flex; align-items: center; justify-content: center; 
            font-size: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
            transition: all 0.3s ease; font-family: Arial, sans-serif; border: none; color: white;
        }}
        .aboro-chat-button:hover {{ transform: scale(1.1); background: #5a67d8; }}
        .aboro-chat-container {{ 
            position: fixed; bottom: 20px; right: 20px; z-index: 9999; 
            width: 400px; height: 600px; background: white; border-radius: 10px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.15); display: none; flex-direction: column; 
            font-family: Arial, sans-serif; overflow: hidden;
        }}
        .aboro-chat-header {{ 
            background: #667eea; color: white; padding: 15px; text-align: center; 
            font-weight: 600; position: relative;
        }}
        .aboro-chat-close {{ 
            position: absolute; top: 10px; right: 15px; background: none; border: none; 
            color: white; font-size: 20px; cursor: pointer; width: 30px; height: 30px; 
            border-radius: 50%;
        }}
        .aboro-chat-messages {{ 
            flex: 1; overflow-y: auto; padding: 15px; background: #f8f9fa;
        }}
        .aboro-chat-input-area {{ 
            padding: 15px; border-top: 1px solid #dee2e6; background: white;
        }}
        .aboro-chat-input {{ 
            width: 100%; padding: 10px; border: 1px solid #ced4da; border-radius: 20px; 
            font-size: 14px; outline: none;
        }}
        .aboro-message {{ margin-bottom: 10px; }}
        .aboro-message-visitor {{ text-align: right; }}
        .aboro-message-agent {{ text-align: left; }}
        .aboro-message-content {{ 
            display: inline-block; padding: 8px 12px; border-radius: 15px; 
            max-width: 80%; word-wrap: break-word; font-size: 14px;
        }}
        .aboro-message-visitor .aboro-message-content {{ background: #667eea; color: white; }}
        .aboro-message-agent .aboro-message-content {{ background: #e9ecef; color: #495057; }}
    `;
    
    // Add CSS
    var styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
    
    // Create Chat Button
    var chatButton = document.createElement('button');
    chatButton.className = 'aboro-chat-button';
    chatButton.innerHTML = '💬';
    
    // Create Chat Container
    var chatContainer = document.createElement('div');
    chatContainer.className = 'aboro-chat-container';
    chatContainer.innerHTML = `
        <div class="aboro-chat-header">
            Live Chat Support
            <button class="aboro-chat-close">×</button>
        </div>
        <div class="aboro-chat-messages" id="aboro-messages"></div>
        <div class="aboro-chat-input-area">
            <input type="text" class="aboro-chat-input" id="aboro-input" placeholder="Nachricht eingeben...">
        </div>
    `;
    
    // Event Handlers
    chatButton.addEventListener('click', openChat);
    chatContainer.querySelector('.aboro-chat-close').addEventListener('click', closeChat);
    chatContainer.querySelector('#aboro-input').addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') sendMessage();
    }});
    
    function openChat() {{
        chatContainer.style.display = 'flex';
        chatButton.style.display = 'none';
        if (!currentSessionId) startChatSession();
    }}
    
    function closeChat() {{
        chatContainer.style.display = 'none';
        chatButton.style.display = 'flex';
    }}
    
    function startChatSession() {{
        fetch(CHAT_API_BASE + '/start/', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                session_id: 'web-' + Date.now(),
                name: 'Website Besucher',
                email: 'besucher@website.com',
                message: 'Hallo, ich brauche Hilfe.',
                page_url: window.location.href
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                currentSessionId = data.session_id;
                startMessagePolling();
            }}
        }})
        .catch(error => console.error('Chat start error:', error));
    }}
    
    function sendMessage() {{
        var input = document.getElementById('aboro-input');
        var message = input.value.trim();
        if (!message || !currentSessionId) return;
        
        input.value = '';
        addMessage(message, true, 'Sie');
        
        fetch(CHAT_API_BASE + '/send/', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                session_id: currentSessionId,
                message: message
            }})
        }})
        .catch(error => console.error('Send message error:', error));
    }}
    
    function addMessage(content, isVisitor, sender) {{
        var messagesDiv = document.getElementById('aboro-messages');
        var messageDiv = document.createElement('div');
        messageDiv.className = 'aboro-message ' + (isVisitor ? 'aboro-message-visitor' : 'aboro-message-agent');
        messageDiv.innerHTML = `<div class="aboro-message-content">${{content}}</div>`;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }}
    
    function startMessagePolling() {{
        messageCheckInterval = setInterval(checkMessages, 3000);
    }}
    
    function checkMessages() {{
        if (!currentSessionId) return;
        
        fetch(CHAT_API_BASE + '/messages/' + currentSessionId + '/')
        .then(response => response.json())
        .then(data => {{
            if (data.success && data.messages) {{
                var messagesDiv = document.getElementById('aboro-messages');
                messagesDiv.innerHTML = '';
                data.messages.forEach(msg => {{
                    addMessage(msg.message, msg.is_from_visitor, msg.sender_name);
                }});
            }}
        }})
        .catch(error => console.error('Check messages error:', error));
    }}
    
    // Add to page
    document.body.appendChild(chatButton);
    document.body.appendChild(chatContainer);
}})();
</script>'''

    context = {
        'form': form,
        'system_settings': system_settings,
        'chat_settings': chat_settings,
        'site_url': site_url,
        'widget_url': widget_url,
        'embed_code': embed_code,
        'js_embed_code': js_embed_code,
        'native_js_code': native_js_code,
    }
    
    return render(request, 'main/admin_settings.html', context)


def debug_widget_codes(request):
    """Debug view to show widget codes without login requirement"""
    from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
    from apps.helpdesk.helpdesk_apps.chat.models import ChatSettings
    
    # Get settings
    system_settings = SystemSettings.get_settings()
    chat_settings = ChatSettings.get_settings()
    
    # Generate widget codes
    # Use site_url from database if available, otherwise use Django settings
    site_url = system_settings.site_url if system_settings.site_url else getattr(settings, 'SITE_URL', 'http://localhost:8000')
    prefix = getattr(settings, 'HELPDESK_URL_PREFIX', '')
    widget_url = f"{site_url}{prefix}/chat/widget/"
    
    embed_code = f'''<!-- Aboro-IT Helpdesk Live Chat Widget -->
<iframe src="{widget_url}" 
        width="400" 
        height="600" 
        frameborder="0" 
        style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
</iframe>'''

    js_embed_code = f'''<!-- Aboro-IT Helpdesk Live Chat Widget (JavaScript) -->
<script>
(function() {{
    var iframe = document.createElement('iframe');
    iframe.src = '{widget_url}';
    iframe.width = '400';
    iframe.height = '600';
    iframe.frameBorder = '0';
    iframe.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);';
    document.body.appendChild(iframe);
}})();
</script>'''
    
    context = {
        'site_url': site_url,
        'widget_url': widget_url,
        'embed_code': embed_code,
        'js_embed_code': js_embed_code,
        'system_settings': system_settings,
        'chat_settings': chat_settings,
    }
    
    return render(request, 'main/debug_widget.html', context)


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'))


@login_required
@user_passes_test(is_admin)
def manage_license(request):
    """Manage license code - integrated into main app"""
    from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
    from apps.helpdesk.helpdesk_apps.admin_panel.forms import LicenseForm
    from apps.helpdesk.helpdesk_apps.api.license_manager import LicenseManager
    
    settings_obj = SystemSettings.get_settings()
    license_info = None
    form = None

    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            license_code = form.cleaned_data['license_code']
            license_info = form.get_license_info()

            # Update system settings - Only license code and validation timestamp
            # All other license info is now automatically derived from the license code
            settings_obj.license_code = license_code
            settings_obj.license_last_validated = timezone_now()
            settings_obj.updated_by = request.user
            settings_obj.save()

            messages.success(
                request,
                f'Lizenz erfolgreich aktiviert! Produkt: {license_info.get("product_name")}, '
                f'Gültig bis: {license_info.get("expiry_date")}'
            )
            return redirect('main:manage_license')
    else:
        form = LicenseForm()
        # Load current license info automatically from license code
        license_info = settings_obj.get_license_info()

    context = {
        'page_title': 'Lizenzverwaltung',
        'form': form,
        'settings': settings_obj,
        'license_info': license_info,
    }

    return render(request, 'admin/manage_license.html', context)


# ====================================================================
# USER MANAGEMENT - Simplified interface instead of Django Admin
# ====================================================================

@login_required
@user_passes_test(is_admin)
def user_management(request):
    """User management overview - simple interface"""
    # Search functionality
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    users = User.objects.all().order_by('-created_at')
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users, 25)  # 25 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'admins': User.objects.filter(role='admin').count(),
        'agents': User.objects.filter(role='support_agent').count(),
        'customers': User.objects.filter(role='customer').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'stats': stats,
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'admin/user_management.html', context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Create new user - simplified form"""
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'customer')
        support_level = request.POST.get('support_level')
        password = request.POST.get('password', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()
        
        # Basic validation
        errors = []
        if not username:
            errors.append('Benutzername ist erforderlich')
        elif User.objects.filter(username=username).exists():
            errors.append('Benutzername bereits vergeben')
            
        if not email:
            errors.append('E-Mail ist erforderlich')
        elif User.objects.filter(email=email).exists():
            errors.append('E-Mail bereits vergeben')
            
        if not first_name:
            errors.append('Vorname ist erforderlich')
        if not last_name:
            errors.append('Nachname ist erforderlich')
        if not password or len(password) < 6:
            errors.append('Passwort muss mindestens 6 Zeichen lang sein')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    phone=phone,
                    department=department,
                )
                
                # Set support level for agents
                if role == 'support_agent' and support_level:
                    user.support_level = int(support_level)
                    user.save()
                
                messages.success(request, f'Benutzer "{username}" wurde erfolgreich erstellt!')
                return redirect('main:user_management')
                
            except Exception as e:
                messages.error(request, f'Fehler beim Erstellen des Benutzers: {str(e)}')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
        'support_level_choices': User.SUPPORT_LEVEL_CHOICES,
    }
    
    return render(request, 'admin/user_create.html', context)


@login_required
@user_passes_test(is_admin)
def user_edit(request, user_id):
    """Edit user - simplified form"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', user_obj.role)
        support_level = request.POST.get('support_level')
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        
        # Basic validation
        errors = []
        if not username:
            errors.append('Benutzername ist erforderlich')
        elif User.objects.filter(username=username).exclude(id=user_obj.id).exists():
            errors.append('Benutzername bereits vergeben')
            
        if not email:
            errors.append('E-Mail ist erforderlich')
        elif User.objects.filter(email=email).exclude(id=user_obj.id).exists():
            errors.append('E-Mail bereits vergeben')
            
        if not first_name:
            errors.append('Vorname ist erforderlich')
        if not last_name:
            errors.append('Nachname ist erforderlich')
        
        if new_password and len(new_password) < 6:
            errors.append('Neues Passwort muss mindestens 6 Zeichen lang sein')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Update user
                user_obj.username = username
                user_obj.email = email
                user_obj.first_name = first_name
                user_obj.last_name = last_name
                user_obj.role = role
                user_obj.phone = phone
                user_obj.department = department
                
                # Set support level for agents
                if role == 'support_agent' and support_level:
                    user_obj.support_level = int(support_level)
                elif role != 'support_agent':
                    user_obj.support_level = None
                
                # Update password if provided
                if new_password:
                    user_obj.set_password(new_password)
                    user_obj.force_password_change = True
                
                user_obj.save()
                
                messages.success(request, f'Benutzer "{username}" wurde erfolgreich aktualisiert!')
                return redirect('main:user_management')
                
            except Exception as e:
                messages.error(request, f'Fehler beim Aktualisieren des Benutzers: {str(e)}')
    
    context = {
        'user_obj': user_obj,
        'role_choices': User.ROLE_CHOICES,
        'support_level_choices': User.SUPPORT_LEVEL_CHOICES,
    }
    
    return render(request, 'admin/user_edit.html', context)


@login_required
@user_passes_test(is_admin)
def user_delete(request, user_id):
    """Delete user with confirmation"""
    user_obj = get_object_or_404(User, id=user_id)
    
    # Prevent deleting the current user
    if user_obj.id == request.user.id:
        messages.error(request, 'Sie können sich nicht selbst löschen!')
        return redirect('main:user_management')
    
    if request.method == 'POST':
        username = user_obj.username
        try:
            user_obj.delete()
            messages.success(request, f'Benutzer "{username}" wurde erfolgreich gelöscht!')
        except Exception as e:
            messages.error(request, f'Fehler beim Löschen des Benutzers: {str(e)}')
        
        return redirect('main:user_management')
    
    context = {
        'user_obj': user_obj,
    }
    
    return render(request, 'admin/user_delete.html', context)


@login_required
@user_passes_test(is_admin)
def user_toggle_active(request, user_id):
    """Toggle user active status (AJAX)"""
    user_obj = get_object_or_404(User, id=user_id)

    # Prevent deactivating the current user
    if user_obj.id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'Sie können sich nicht selbst deaktivieren!'
        })

    try:
        user_obj.is_active = not user_obj.is_active
        user_obj.save()

        return JsonResponse({
            'success': True,
            'is_active': user_obj.is_active,
            'message': f'Benutzer {"aktiviert" if user_obj.is_active else "deaktiviert"}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ====================================================================
# EASTER EGG - Secret Retro Game
# ====================================================================

@login_required
def retro_game(request):
    """Secret retro runner game - Easter egg for logged in users"""
    return render(request, 'games/retro_runner.html')


@login_required
def virus_kong_game(request):
    """Virus Kong game - Donkey Kong variant"""
    return render(request, 'games/virus_kong.html')


@login_required
def game_save_score(request):
    """Save game score (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})

    try:
        import json
        data = json.loads(request.body)

        score = int(data.get('score', 0))
        level_reached = int(data.get('level', 1))
        coins_collected = int(data.get('coins', 0))
        time_played = int(data.get('time', 0))

        from apps.helpdesk.helpdesk_apps.main.models import GameHighscore

        # Create new highscore entry
        highscore = GameHighscore.objects.create(
            player=request.user,
            score=score,
            level_reached=level_reached,
            coins_collected=coins_collected,
            time_played=time_played
        )

        # Get player's rank
        rank = GameHighscore.objects.filter(score__gt=score).count() + 1

        return JsonResponse({
            'success': True,
            'rank': rank,
            'message': 'Score gespeichert!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def game_get_highscores(request):
    """Get top highscores (AJAX)"""
    try:
        from apps.helpdesk.helpdesk_apps.main.models import GameHighscore

        limit = int(request.GET.get('limit', 10))
        scores = GameHighscore.get_top_scores(limit)

        scores_data = [{
            'rank': idx + 1,
            'player_name': score.player.full_name if hasattr(score.player, 'full_name') else f"{score.player.first_name} {score.player.last_name}",
            'score': score.score,
            'level': score.level_reached,
            'coins': score.coins_collected,
            'date': score.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_current_user': score.player.id == request.user.id
        } for idx, score in enumerate(scores)]

        # Get current player's best score
        player_best = GameHighscore.get_player_best_score(request.user)
        player_best_data = None
        if player_best:
            player_rank = GameHighscore.objects.filter(score__gt=player_best.score).count() + 1
            player_best_data = {
                'rank': player_rank,
                'score': player_best.score,
                'level': player_best.level_reached,
                'coins': player_best.coins_collected,
                'date': player_best.created_at.strftime('%d.%m.%Y %H:%M')
            }

        return JsonResponse({
            'success': True,
            'scores': scores_data,
            'player_best': player_best_data,
            'total_players': GameHighscore.objects.values('player').distinct().count()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def game_save_score_viruskong(request):
    """Save Virus Kong score (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})

    try:
        import json
        data = json.loads(request.body)

        score = int(data.get('score', 0))
        level_reached = int(data.get('level', 1))

        from apps.helpdesk.helpdesk_apps.main.models import VirusKongHighscore

        # Create new highscore entry
        highscore = VirusKongHighscore.objects.create(
            player=request.user,
            score=score,
            level_reached=level_reached
        )

        # Get player's rank
        rank = VirusKongHighscore.objects.filter(score__gt=score).count() + 1

        return JsonResponse({
            'success': True,
            'rank': rank,
            'message': 'Score gespeichert!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def game_get_highscores_viruskong(request):
    """Get top Virus Kong highscores (AJAX)"""
    try:
        from apps.helpdesk.helpdesk_apps.main.models import VirusKongHighscore

        limit = int(request.GET.get('limit', 10))
        scores = VirusKongHighscore.get_top_scores(limit)

        scores_data = [{
            'rank': idx + 1,
            'player_name': score.player.full_name if hasattr(score.player, 'full_name') else f"{score.player.first_name} {score.player.last_name}",
            'score': score.score,
            'level': score.level_reached,
            'date': score.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_current_user': score.player.id == request.user.id
        } for idx, score in enumerate(scores)]

        # Get current player's best score
        player_best = VirusKongHighscore.get_player_best_score(request.user)
        player_best_data = None
        if player_best:
            player_rank = VirusKongHighscore.objects.filter(score__gt=player_best.score).count() + 1
            player_best_data = {
                'rank': player_rank,
                'score': player_best.score,
                'level': player_best.level_reached,
                'date': player_best.created_at.strftime('%d.%m.%Y %H:%M')
            }

        return JsonResponse({
            'success': True,
            'scores': scores_data,
            'player_best': player_best_data,
            'total_players': VirusKongHighscore.objects.values('player').distinct().count()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
