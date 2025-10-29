"""
Утилиты для работы с JWT токенами и безопасностью.
"""
import hashlib
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone


# Настройки JWT
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = getattr(settings, 'JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_LIFETIME = getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', 15)  # минуты
JWT_REFRESH_TOKEN_LIFETIME = getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', 7)  # дни


def generate_access_token(user_id: int) -> tuple[str, datetime]:
    """
    Генерация access токена.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Кортеж (токен, время истечения)
    """
    expires_at = timezone.now() + timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME)
    
    payload = {
        'user_id': user_id,
        'exp': expires_at,
        'iat': timezone.now(),
        'type': 'access',
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires_at


def generate_refresh_token(user_id: int) -> tuple[str, datetime]:
    """
    Генерация refresh токена.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Кортеж (токен, время истечения)
    """
    expires_at = timezone.now() + timedelta(days=JWT_REFRESH_TOKEN_LIFETIME)
    
    payload = {
        'user_id': user_id,
        'exp': expires_at,
        'iat': timezone.now(),
        'type': 'refresh',
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> dict:
    """
    Декодирование и валидация токена.
    
    Args:
        token: JWT токен
        
    Returns:
        Декодированные данные токена
        
    Raises:
        jwt.ExpiredSignatureError: Токен истек
        jwt.InvalidTokenError: Невалидный токен
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError('Токен истек')
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f'Невалидный токен: {str(e)}')


def hash_token(token: str) -> str:
    """
    Хеширование токена для хранения в БД.
    
    Args:
        token: JWT токен
        
    Returns:
        SHA-256 хеш токена
    """
    return hashlib.sha256(token.encode()).hexdigest()


def get_client_ip(request) -> str:
    """
    Получение IP адреса клиента из запроса.
    
    Args:
        request: HTTP запрос
        
    Returns:
        IP адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request) -> str:
    """
    Получение User-Agent из запроса.
    
    Args:
        request: HTTP запрос
        
    Returns:
        User-Agent строка
    """
    return request.META.get('HTTP_USER_AGENT', '')
