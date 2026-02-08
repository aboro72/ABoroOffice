from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


CRM_GROUP_ORGA = "Orga"
CRM_GROUP_MANAGER = "Manager"


def user_in_groups(user, group_names):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=group_names).exists()


def can_view_crm(user):
    return user_in_groups(user, [CRM_GROUP_ORGA, CRM_GROUP_MANAGER])


def can_edit_crm(user):
    return user_in_groups(user, [CRM_GROUP_MANAGER])


class CrmViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow CRM read access for Orga/Manager or staff/superuser."""

    def test_func(self):
        return can_view_crm(self.request.user)


class CrmEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow CRM write access for Manager or staff/superuser."""

    def test_func(self):
        return can_edit_crm(self.request.user)

