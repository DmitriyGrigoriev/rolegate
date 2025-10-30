"""
Views для API аутентификации и авторизации.
"""
import jwt
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import User, Role, UserRole, BusinessElement, AccessRule, Session
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    UserUpdateSerializer,
    RoleSerializer,
    UserRoleSerializer,
    BusinessElementSerializer,
    AccessRuleSerializer,
    RefreshTokenSerializer, TokenSerializer, LoginResponseSerializer, AuthSerializer,
)
from .permissions import IsAuthenticated, IsAdminRole, HasResourcePermission
from .utils import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    hash_token,
    get_client_ip,
    get_user_agent,
)


class AuthViewSet(viewsets.ViewSet):
    """ViewSet для операций аутентификации."""

    serializer_class = AuthSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Ошибка валидации'),
        },
        tags=['Аутентификация'],
        summary='Регистрация нового пользователя',
        description='Создание нового пользователя в системе',
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Регистрация нового пользователя.

        POST /api/auth/register/
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_data = UserSerializer(user).data
        return Response(
            {
                'message': 'Пользователь успешно зарегистрирован',
                'user': user_data,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            400: OpenApiResponse(description='Неверные учетные данные'),
        },
        tags=['Аутентификация'],
        summary='Вход в систему',
        description='Аутентификация по email и паролю. После успешного входа '
                    'используйте полученный access_token в заголовке Authorization: Bearer <token>',
        examples=[
            OpenApiExample(
                name='Успешная аутентификация',
                value={
                    "email": "admin@example.com",
                    "password": "Admin123!"
                },
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Вход в систему.

        POST /api/auth/login/
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Генерируем токены
        access_token, access_expires = generate_access_token(user.id)
        refresh_token, refresh_expires = generate_refresh_token(user.id)

        # Создаем сессию
        Session.objects.create(
            user=user,
            token_hash=hash_token(access_token),
            refresh_token_hash=hash_token(refresh_token),
            expires_at=access_expires,
            refresh_expires_at=refresh_expires,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        # Подготавливаем ответ
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 15 * 60,  # 15 минут в секундах
            'token_type': 'Bearer',
        }

        user_data = UserSerializer(user).data

        return Response({
            'message': 'Успешный вход',
            'user': user_data,
            'tokens': token_data,
        })

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(description='Успешный выход'),
        },
        tags=['Аутентификация'],
        summary='Выход из системы',
        description='Деактивация текущей сессии',
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Выход из системы.

        POST /api/auth/logout/
        """
        # Извлекаем токен из заголовка
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            token_hash = hash_token(token)

            # Деактивируем сессию
            Session.objects.filter(
                user=request.user,
                token_hash=token_hash,
                is_active=True,
            ).update(is_active=False)

        return Response({'message': 'Успешный выход'})

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: TokenSerializer,
            401: OpenApiResponse(description='Невалидный или истекший токен'),
        },
        tags=['Аутентификация'],
        summary='Обновление access токена',
        description='Получение нового access токена используя refresh токен',
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh(self, request):
        """
        Обновление access токена.

        POST /api/auth/refresh/
        """
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            # Декодируем refresh токен
            payload = decode_token(refresh_token)

            # Проверяем тип токена
            if payload.get('type') != 'refresh':
                return Response(
                    {'error': 'Невалидный тип токена'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_id = payload.get('user_id')
            refresh_token_hash = hash_token(refresh_token)

            # Находим активную сессию
            session = Session.objects.filter(
                user_id=user_id,
                refresh_token_hash=refresh_token_hash,
                is_active=True,
            ).first()

            if not session or session.is_refresh_expired():
                return Response(
                    {'error': 'Refresh токен истек или невалиден'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Генерируем новые токены
            access_token, access_expires = generate_access_token(user_id)
            new_refresh_token, refresh_expires = generate_refresh_token(user_id)

            # Обновляем сессию
            session.token_hash = hash_token(access_token)
            session.refresh_token_hash = hash_token(new_refresh_token)
            session.expires_at = access_expires
            session.refresh_expires_at = refresh_expires
            session.save()

            token_data = {
                'access_token': access_token,
                'refresh_token': new_refresh_token,
                'expires_in': 15 * 60,
                'token_type': 'Bearer',
            }

            return Response({'tokens': token_data})

        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    @extend_schema(
        request=None,
        responses={
            200: UserSerializer,
        },
        tags=['Профиль'],
        summary='Получить информацию о текущем пользователе',
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Получение информации о текущем пользователе.

        GET /api/auth/me/
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Обновление профиля текущего пользователя.

        PUT/PATCH /api/auth/me/
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH',
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = UserSerializer(request.user).data
        return Response({
            'message': 'Профиль успешно обновлен',
            'user': user_data,
        })

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        """
        Мягкое удаление аккаунта текущего пользователя.

        DELETE /api/auth/me/
        """
        user = request.user

        # Мягкое удаление - деактивация пользователя
        user.is_active = False
        user.save()

        # Деактивируем все сессии пользователя
        Session.objects.filter(user=user, is_active=True).update(is_active=False)

        return Response({
            'message': 'Аккаунт успешно удален',
        })


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями (только для администраторов)."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        """Получение queryset с prefetch для оптимизации."""
        return User.objects.prefetch_related('user_roles__role').all()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='role_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Role ID'
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """
        Назначить роль пользователю.

        POST /api/users/{id}/assign-role/
        """
        user = self.get_object()
        role_id = request.data.get('role_id')

        if not role_id:
            return Response(
                {'error': 'role_id обязателен'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response(
                {'error': 'Роль не найдена'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверяем, не назначена ли уже эта роль
        if UserRole.objects.filter(user=user, role=role).exists():
            return Response(
                {'error': 'Роль уже назначена этому пользователю'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Назначаем роль
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            assigned_by=request.user,
        )

        serializer = UserRoleSerializer(user_role)
        return Response({
            'message': 'Роль успешно назначена',
            'user_role': serializer.data,
        })

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='role_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Role ID'
            )
        ]
    )
    @action(detail=True, methods=['delete'], url_path='roles/(?P<role_id>[^/.]+)')
    def revoke_role(self, request, pk=None, role_id=None):
        """
        Отозвать роль у пользователя.

        DELETE /api/users/{id}/roles/{role_id}/
        """
        user = self.get_object()

        try:
            user_role = UserRole.objects.get(user=user, role_id=role_id)
            user_role.delete()
            return Response({'message': 'Роль успешно отозвана'})
        except UserRole.DoesNotExist:
            return Response(
                {'error': 'Роль не найдена у этого пользователя'},
                status=status.HTTP_404_NOT_FOUND,
            )


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ролями (только для администраторов)."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]


class BusinessElementViewSet(viewsets.ModelViewSet):
    """ViewSet для управления бизнес-элементами (только для администраторов)."""

    queryset = BusinessElement.objects.all()
    serializer_class = BusinessElementSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]


class AccessRuleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления правилами доступа (только для администраторов)."""

    queryset = AccessRule.objects.select_related('role', 'element').all()
    serializer_class = AccessRuleSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
