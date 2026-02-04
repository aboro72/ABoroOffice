from django.db import connection, models


class ZoneinfoSafeDateHierarchyMixin:
    """
    Gracefully disable ModelAdmin.date_hierarchy when the database lacks
    timezone tables, preventing MySQL's CONVERT_TZ() from returning NULL.
    """

    def get_list_filter(self, request):
        original = super().get_list_filter(request)
        list_filter = list(original)
        if not connection.features.has_zoneinfo_database:
            cleaned_filters = []
            model = getattr(self, "model", None)
            opts = model._meta if model else None
            for item in list_filter:
                field_name = None
                if isinstance(item, str):
                    field_name = item
                elif isinstance(item, (list, tuple)) and item:
                    field_name = item[0]
                if field_name and opts:
                    try:
                        field = opts.get_field(field_name)
                    except Exception:
                        field = None
                    if isinstance(field, models.DateTimeField):
                        continue
                cleaned_filters.append(item)
            if isinstance(original, tuple):
                return tuple(cleaned_filters)
            return cleaned_filters
        return original

    def get_changelist_instance(self, request):
        if connection.features.has_zoneinfo_database:
            return super().get_changelist_instance(request)
        original_hierarchy = getattr(self, "date_hierarchy", None)
        try:
            self.date_hierarchy = None
            return super().get_changelist_instance(request)
        finally:
            self.date_hierarchy = original_hierarchy
