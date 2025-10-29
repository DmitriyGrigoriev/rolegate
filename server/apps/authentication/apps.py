"""
Конфигурация приложения authentication.
"""
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Конфигурация приложения authentication."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'server.apps.authentication'
    verbose_name = 'Аутентификация и авторизация'
    
    def ready(self):
        """Инициализация приложения."""
        # Импортируем сигналы если будут нужны
        pass
