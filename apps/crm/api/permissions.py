from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.crm.permissions import can_view_crm, can_edit_crm


class CrmReadWritePermission(BasePermission):
    """
    Read: Orga/Manager (or staff/superuser).
    Write: Manager (or staff/superuser).
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return can_view_crm(user)
        return can_edit_crm(user)
