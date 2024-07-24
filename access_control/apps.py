from django.apps import AppConfig
from django.conf import settings

class AccessControlConfig(AppConfig):
    name = 'access_control'

    def ready(self):
        from .utils import load_databases, check_database_connections
        settings.DATABASES.update(load_databases())
        check_database_connections(settings.DATABASES)
