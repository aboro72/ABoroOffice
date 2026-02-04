"""
Chat Widget Middleware
======================

Middleware für Chat Widget Cross-Origin Support
"""
from django.conf import settings
from django.http import HttpResponse


class ChatWidgetFrameMiddleware:
    """
    Middleware um Chat Widget iframe-Embedding für erlaubte Domains zu ermöglichen
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Nur für Chat Widget URLs
        if request.path.startswith('/chat/widget/'):
            # Hole Referrer (die Domain, die das Widget einbettet)
            referrer = request.META.get('HTTP_REFERER', '')
            origin = request.META.get('HTTP_ORIGIN', '')
            
            # Liste der erlaubten Domains aus Chat-Einstellungen und Django Settings
            from .models import ChatSettings
            chat_settings = ChatSettings.get_settings()
            
            # Domains aus Chat-Einstellungen (komma-getrennt)
            chat_domains = [d.strip() for d in chat_settings.allowed_domains.split(',') if d.strip()]
            
            # Domains aus Django Settings
            django_domains = getattr(settings, 'ALLOWED_IFRAME_ORIGINS', [])
            
            # Kombiniere beide Listen
            allowed_origins = chat_domains + django_domains
            
            # Prüfe ob Referrer oder Origin in erlaubten Domains ist
            is_allowed = False
            for allowed in allowed_origins:
                if referrer.startswith(allowed) or origin == allowed:
                    is_allowed = True
                    break
            
            if is_allowed:
                # Entferne X-Frame-Options komplett für erlaubte Domains
                # Das ist nötig, weil Firefox ALLOW-FROM nicht richtig unterstützt
                if 'X-Frame-Options' in response:
                    del response['X-Frame-Options']
                
                # Verwende nur moderne CSP (Content-Security-Policy)
                # Firefox respektiert frame-ancestors besser als X-Frame-Options
                csp_origins = []
                for allowed in allowed_origins:
                    # Entferne Protokoll wenn vorhanden für CSP
                    if allowed.startswith('http'):
                        csp_origins.append(allowed)
                    else:
                        csp_origins.append(f"https://{allowed}")
                
                response['Content-Security-Policy'] = f"frame-ancestors 'self' {' '.join(csp_origins)}"
                
                # CORS Headers für API-Calls
                response['Access-Control-Allow-Origin'] = origin or referrer
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization'
            else:
                # Standard Sicherheit: kein iframe-Embedding
                response['X-Frame-Options'] = 'DENY'
                response['Content-Security-Policy'] = "frame-ancestors 'none'"
        
        return response


class ChatCorsMiddleware:
    """
    CORS Middleware speziell für Chat API Endpoints mit Firefox-spezifischen Fixes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Get origin and user agent
        origin = request.META.get('HTTP_ORIGIN', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_firefox = 'Firefox' in user_agent
        
        # Handle preflight requests
        if request.method == 'OPTIONS' and (request.path.startswith('/chat/api/') or request.path.startswith('/chat/widget')):
            response = HttpResponse()
            
            # Hole erlaubte Domains aus Chat-Einstellungen
            from .models import ChatSettings
            chat_settings = ChatSettings.get_settings()
            chat_domains = [d.strip() for d in chat_settings.allowed_domains.split(',') if d.strip()]
            django_domains = getattr(settings, 'ALLOWED_IFRAME_ORIGINS', [])
            allowed_origins = chat_domains + django_domains
            
            # Firefox-freundliche CORS-Header für alle erlaubten Domains
            allow_any = (not allowed_origins) or any(origin.startswith(allowed) for allowed in allowed_origins)
            if allow_any or is_firefox:
                response['Access-Control-Allow-Origin'] = origin or '*'
                response['Access-Control-Allow-Credentials'] = 'false' if is_firefox else 'true'
                response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
                response['Access-Control-Allow-Headers'] = 'Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, X-Requested-With'
                response['Access-Control-Max-Age'] = '86400'
                
                # Firefox-spezifische Header
                if is_firefox:
                    response['Vary'] = 'Origin'
                    response['Access-Control-Expose-Headers'] = 'Content-Length'
            
            return response
        
        response = self.get_response(request)
        
        # Add CORS headers to all chat-related responses
        if (request.path.startswith('/chat/api/') or 
            request.path.startswith('/chat/widget') or 
            request.path.endswith('widget.js') or
            request.path.endswith('debug-widget.js')):
            
            # Hole erlaubte Domains aus Chat-Einstellungen
            from .models import ChatSettings
            try:
                chat_settings = ChatSettings.get_settings()
                chat_domains = [d.strip() for d in chat_settings.allowed_domains.split(',') if d.strip()]
            except:
                chat_domains = ['https://aboro-it.net', 'https://www.aboro-it.net']
                
            django_domains = getattr(settings, 'ALLOWED_IFRAME_ORIGINS', [])
            allowed_origins = chat_domains + django_domains
            
            # Sehr permissive CORS-Header für Firefox-Kompatibilität
            allow_any = (not allowed_origins) or any(origin.startswith(allowed) for allowed in allowed_origins)
            if allow_any or is_firefox:
                response['Access-Control-Allow-Origin'] = origin or '*'
                response['Access-Control-Allow-Credentials'] = 'false' if is_firefox else 'true'
                response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, X-Requested-With'
                
                # Firefox-spezifische Header
                if is_firefox:
                    response['Vary'] = 'Origin'
                    response['Cache-Control'] = 'no-cache'
                    # Entferne potenziell problematische Header
                    if 'X-Frame-Options' in response:
                        del response['X-Frame-Options']
                    if 'Content-Security-Policy' in response:
                        del response['Content-Security-Policy']
        
        return response
