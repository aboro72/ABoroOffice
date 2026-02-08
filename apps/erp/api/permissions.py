from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.erp.permissions import can_view_erp, can_edit_erp


class ErpReadWritePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return can_view_erp(request.user)
        return can_edit_erp(request.user)
