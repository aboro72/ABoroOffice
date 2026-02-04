"""
Views for the classroom app.
"""

from django.views.generic import TemplateView
from apps.licensing.mixins import LicenseRequiredMixin


class ClassroomIndexView(LicenseRequiredMixin, TemplateView):
    """Simple landing page until full classroom views are implemented."""

    license_feature = "classroom"
    template_name = "classroom/index.html"
