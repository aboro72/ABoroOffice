"""
HTTPS Redirect Middleware
Verhindert HTTPS-Fehler im Development Server
"""
from django.http import HttpResponseRedirect
from django.conf import settings

class HTTPSRedirectMiddleware:
    """
    Middleware um HTTPS-Requests auf HTTP umzuleiten in Development
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Nur in DEBUG/Development Mode aktiv
        if settings.DEBUG:
            # Prüfe ob Request über HTTPS kam
            if request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
                # Umleitung auf HTTP
                http_url = request.build_absolute_uri().replace('https://', 'http://')
                return HttpResponseRedirect(http_url)
        
        response = self.get_response(request)
        return response


class HTTPSToHTTPRedirectMiddleware:
    """
    Alternative Middleware - einfacher Ansatz
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG and request.is_secure():
            # Baue HTTP URL
            http_url = f"http://{request.get_host()}{request.get_full_path()}"
            return HttpResponseRedirect(http_url)
        
        return self.get_response(request)