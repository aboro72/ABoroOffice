"""
Mixins for license enforcement in class-based views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect


class LicenseRequiredMixin(LoginRequiredMixin):
    """
    Mixin for class-based views that require a specific license feature.

    Usage:
        class MyView(LicenseRequiredMixin, TemplateView):
            license_feature = 'classroom'
            template_name = 'myapp/template.html'
    """

    license_feature = None

    def test_func(self):
        """Check if user has access to the required feature."""
        if not self.license_feature:
            return True

        if hasattr(self.request.user, 'can_access_feature'):
            return self.request.user.can_access_feature(self.license_feature)
        return False

    def handle_no_permission(self):
        """Handle no permission case."""
        messages.error(
            self.request,
            f'Feature "{self.license_feature}" is not available in your license plan. '
            'Please upgrade to access this feature.'
        )
        # Redirect to dashboard or home
        return redirect('admin:index')


class StaffLicenseRequiredMixin(UserPassesTestMixin, LicenseRequiredMixin):
    """
    Mixin that requires both staff status and a license feature.
    """

    def test_func(self):
        """Check both staff status and license feature."""
        if not self.request.user.is_staff:
            return False

        if self.license_feature:
            return self.request.user.can_access_feature(self.license_feature)

        return True

    def handle_no_permission(self):
        """Handle no permission case."""
        if not self.request.user.is_staff:
            messages.error(
                self.request,
                'You do not have permission to access this page. '
                'Staff access is required.'
            )
        else:
            messages.error(
                self.request,
                f'Feature "{self.license_feature}" is not available in your license plan.'
            )
        return redirect('admin:index')
