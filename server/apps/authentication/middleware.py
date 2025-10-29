"""
Middleware для аутентификации пользователя по JWT токену.
"""
import jwt
from django.utils.functional import SimpleLazyObject

from .models import User, Session
from .utils import decode_token, hash_token


def get_user_from_token(request):
    """
    Извлечение пользователя из JWT токена в заголовке Authorization.
    
    Args:
        request: HTTP запрос
        
    Returns:
        Объект User или None
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Убираем "Bearer "
    
    try:
        # Декодируем токен
        payload = decode_token(token)
        
        # Проверяем тип токена
        if payload.get('type') != 'access':
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        # Проверяем существование активной сессии
        token_hash = hash_token(token)
        session_exists = Session.objects.filter(
            user_id=user_id,
            token_hash=token_hash,
            is_active=True,
        ).exists()
        
        if not session_exists:
            return None
        
        # Загружаем пользователя с его ролями
        user = User.objects.prefetch_related(
            'user_roles__role__access_rules__element'
        ).get(
            id=user_id,
            is_active=True,
        )
        
        return user
        
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, User.DoesNotExist):
        return None


class JWTAuthenticationMiddleware:
    """
    Middleware для аутентификации пользователя по JWT токену.
    
    Извлекает токен из заголовка Authorization и устанавливает
    request.user для последующей обработки запроса.
    """
    
    def __init__(self, get_response):
        """Инициализация middleware."""
        self.get_response = get_response
    
    def __call__(self, request):
        """Обработка запроса."""
        # Устанавливаем user как lazy object для оптимизации
        request.user = SimpleLazyObject(lambda: get_user_from_token(request))
        
        response = self.get_response(request)
        return response
