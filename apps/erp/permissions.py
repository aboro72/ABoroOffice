from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


ERP_GROUP_ORGA = "Orga"
ERP_GROUP_MANAGER = "Manager"


def user_in_groups(user, group_names):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=group_names).exists()


def can_view_erp(user):
    settings_obj = SystemSettings.get_settings()
    groups = settings_obj.erp_view_groups or [ERP_GROUP_ORGA, ERP_GROUP_MANAGER]
    return user_in_groups(user, groups)


def can_edit_erp(user):
    settings_obj = SystemSettings.get_settings()
    groups = settings_obj.erp_edit_groups or [ERP_GROUP_MANAGER]
    return user_in_groups(user, groups)


class ErpViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_view_erp(self.request.user)


class ErpEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_edit_erp(self.request.user)
