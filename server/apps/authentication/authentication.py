"""
DRF Authentication классы для JWT токенов.
"""
import jwt
from rest_framework import authentication, exceptions

from .models import User, Session
from .utils import decode_token, hash_token


class JWTAuthentication(authentication.BaseAuthentication):
    """
    DRF Authentication класс для JWT токенов.

    Извлекает токен из заголовка Authorization: Bearer <token>
    и аутентифицирует пользователя.
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        """
        Аутентификация пользователя по JWT токену.

        Args:
            request: HTTP запрос

        Returns:
            tuple (user, token) если токен валиден, иначе None
        """
        auth_header = authentication.get_authorization_header(request).decode('utf-8')

        if not auth_header:
            return None

        auth_parts = auth_header.split()

        if len(auth_parts) == 0:
            return None

        if auth_parts[0].lower() != self.keyword.lower():
            return None

        if len(auth_parts) == 1:
            raise exceptions.AuthenticationFailed('Токен не предоставлен')

        if len(auth_parts) > 2:
            raise exceptions.AuthenticationFailed('Некорректный формат токена')

        token = auth_parts[1]

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        """
        Проверка и декодирование JWT токена.

        Args:
            token: JWT токен

        Returns:
            tuple (user, token)

        Raises:
            AuthenticationFailed: если токен невалиден
        """
        try:
            # Декодируем токен
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Токен истек')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Невалидный токен')

        # Проверяем тип токена
        if payload.get('type') != 'access':
            raise exceptions.AuthenticationFailed('Неверный тип токена')

        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('Токен не содержит user_id')

        # Проверяем существование активной сессии
        token_hash = hash_token(token)
        session_exists = Session.objects.filter(
            user_id=user_id,
            token_hash=token_hash,
            is_active=True,
        ).exists()

        if not session_exists:
            raise exceptions.AuthenticationFailed('Сессия не найдена или неактивна')

        # Загружаем пользователя с его ролями
        try:
            user = User.objects.prefetch_related(
                'user_roles__role__access_rules__element'
            ).get(
                id=user_id,
                is_active=True,
            )
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Пользователь не найден')

        return (user, token)

    def authenticate_header(self, request):
        """
        Возвращает строку для заголовка WWW-Authenticate в ответе 401.
        """
        return self.keyword
