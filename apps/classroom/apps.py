from django.apps import AppConfig


class ClassroomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.classroom'
    verbose_name = 'Classroom Management (Pit-Kalendar)'

    def ready(self):
        import apps.classroom.signals
