from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


MARKETING_GROUP_ORGA = "Orga"
MARKETING_GROUP_MANAGER = "Manager"


def user_in_groups(user, group_names):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=group_names).exists()


def can_view_marketing(user):
    settings_obj = SystemSettings.get_settings()
    groups = settings_obj.marketing_view_groups or [MARKETING_GROUP_ORGA, MARKETING_GROUP_MANAGER]
    return user_in_groups(user, groups)


def can_edit_marketing(user):
    settings_obj = SystemSettings.get_settings()
    groups = settings_obj.marketing_edit_groups or [MARKETING_GROUP_MANAGER]
    return user_in_groups(user, groups)


def can_approve_marketing(user):
    settings_obj = SystemSettings.get_settings()
    groups = settings_obj.marketing_approve_groups or [MARKETING_GROUP_ORGA, MARKETING_GROUP_MANAGER]
    return user_in_groups(user, groups)


class MarketingViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_view_marketing(self.request.user)


class MarketingEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_edit_marketing(self.request.user)
