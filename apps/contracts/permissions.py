from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


CONTRACTS_GROUP_ORGA = "Orga"
CONTRACTS_GROUP_MANAGER = "Manager"


def user_in_groups(user, group_names):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=group_names).exists()


def can_view_contracts(user):
    return user_in_groups(user, [CONTRACTS_GROUP_ORGA, CONTRACTS_GROUP_MANAGER])


def can_edit_contracts(user):
    return user_in_groups(user, [CONTRACTS_GROUP_MANAGER])


class ContractsViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_view_contracts(self.request.user)


class ContractsEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return can_edit_contracts(self.request.user)
