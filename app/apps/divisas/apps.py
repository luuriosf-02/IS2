from django.apps import AppConfig

class DivisasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.divisas'

    def ready(self):
        import apps.divisas.signals 