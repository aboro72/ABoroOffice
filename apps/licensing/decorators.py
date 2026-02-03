"""
Decorators for license enforcement.
Used to restrict access to features based on license tier.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from .license_manager import LicenseManager


def license_required(feature):
    """
    Decorator to require a specific feature to be licensed.

    Args:
        feature: Feature code to check (e.g., 'classroom', 'helpdesk_tickets', etc.)

    Usage:
        @login_required
        @license_required('classroom')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return redirect('login')

            # Check if feature is accessible
            if not request.user.can_access_feature(feature):
                messages.error(
                    request,
                    f'Feature "{feature}" is not available in your license plan. '
                    'Please upgrade your plan to access this feature.'
                )
                return HttpResponseForbidden(
                    f'Feature "{feature}" requires a higher license tier.'
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def license_feature_check(feature):
    """
    Alternative decorator that checks license features.
    Can be used for class-based views and other purposes.

    Args:
        feature: Feature code to check

    Returns:
        bool: True if feature is available, False otherwise
    """
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            if hasattr(user, 'can_access_feature'):
                return user.can_access_feature(feature)
            return False
        return wrapper
    return decorator
