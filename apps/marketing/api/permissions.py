from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.marketing.permissions import can_view_marketing, can_edit_marketing


class MarketingReadWritePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return can_view_marketing(request.user)
        return can_edit_marketing(request.user)
