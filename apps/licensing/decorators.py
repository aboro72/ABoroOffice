"""
Decorators for license enforcement.
Used to restrict access to features based on license tier.
"""

import logging
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import View

logger = logging.getLogger('licensing')


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
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")

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


class LicenseRequiredMixin:
    """
    Mixin for class-based views to require a specific license feature.

    Usage:
        class MyView(LicenseRequiredMixin, View):
            required_feature = 'approvals'

            def get(self, request):
                pass
    """

    required_feature = None  # Override this in subclass

    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            logger.warning(
                f"Unauthenticated access attempt to {self.required_feature}"
            )
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        # Check if feature is specified
        if not self.required_feature:
            return super().dispatch(request, *args, **kwargs)

        # Check if license is enabled in settings
        from django.conf import settings
        license_check_enabled = getattr(settings, 'LICENSE_CHECK_ENABLED', True)

        if not license_check_enabled:
            # License checking disabled, allow access
            return super().dispatch(request, *args, **kwargs)

        # Check if user can access feature
        if not request.user.can_access_feature(self.required_feature):
            logger.warning(
                f"Unauthorized access by {request.user} to feature {self.required_feature}"
            )

            # Return JSON error if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': f'Feature "{self.required_feature}" not available',
                    'feature': self.required_feature,
                }, status=403)

            # Otherwise return HTML error
            return HttpResponseForbidden(
                f'Feature "{self.required_feature}" is not available in your current license.'
            )

        return super().dispatch(request, *args, **kwargs)


class ApproverRequiredMixin:
    """
    Mixin for class-based views to require is_approver status.

    Usage:
        class MyView(ApproverRequiredMixin, View):
            def get(self, request):
                pass
    """

    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated access attempt to approval action")
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        # Check if user is approver
        if not request.user.is_approver and not request.user.is_staff:
            logger.warning(
                f"Non-approver access by {request.user} to approval action"
            )

            # Return JSON error if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'You do not have permission to approve requests',
                }, status=403)

            # Otherwise return HTML error
            return HttpResponseForbidden(
                'You do not have the required permissions.'
            )

        return super().dispatch(request, *args, **kwargs)
