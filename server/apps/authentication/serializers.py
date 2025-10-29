"""
Сериализаторы для системы аутентификации и авторизации.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User, Role, UserRole, BusinessElement, AccessRule


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя."""

    roles = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'is_active',
            'roles',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_roles(self, obj):
        """Получение ролей пользователя."""
        return [
            {
                'id': ur.role.id,
                'name': ur.role.name,
                'code': ur.role.code,
            }
            for ur in obj.user_roles.select_related('role').all()
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'middle_name',
        ]

    def validate(self, attrs):
        """Валидация данных."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Пароли не совпадают',
            })
        return attrs

    def create(self, validated_data):
        """Создание пользователя."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)

        # Автоматически назначаем роль "user"
        try:
            user_role = Role.objects.get(code='user')
            UserRole.objects.create(user=user, role=user_role)
        except Role.DoesNotExist:
            pass

        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для входа в систему."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        """Валидация учетных данных."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Проверяем существование пользователя
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError('Неверный email или пароль')

            # Проверяем активность
            if not user.is_active:
                raise serializers.ValidationError(
                    'Аккаунт деактивирован'
                )

            # Проверяем пароль
            if not user.check_password(password):
                raise serializers.ValidationError('Неверный email или пароль')

            attrs['user'] = user
        else:
            raise serializers.ValidationError('Email и пароль обязательны')

        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля пользователя."""

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'middle_name',
        ]


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для роли."""

    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id',
            'name',
            'code',
            'description',
            'users_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_users_count(self, obj):
        """Количество пользователей с этой ролью."""
        return obj.user_roles.count()


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для назначения роли пользователю."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_email = serializers.EmailField(
        source='assigned_by.email',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = UserRole
        fields = [
            'id',
            'user',
            'user_email',
            'role',
            'role_name',
            'assigned_at',
            'assigned_by',
            'assigned_by_email',
        ]
        read_only_fields = ['id', 'assigned_at', 'assigned_by']


class BusinessElementSerializer(serializers.ModelSerializer):
    """Сериализатор для бизнес-элемента."""

    rules_count = serializers.SerializerMethodField()

    class Meta:
        model = BusinessElement
        fields = [
            'id',
            'name',
            'code',
            'description',
            'rules_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_rules_count(self, obj):
        """Количество правил доступа к этому элементу."""
        return obj.access_rules.count()


class AccessRuleSerializer(serializers.ModelSerializer):
    """Сериализатор для правила доступа."""

    role_name = serializers.CharField(source='role.name', read_only=True)
    element_name = serializers.CharField(source='element.name', read_only=True)

    class Meta:
        model = AccessRule
        fields = [
            'id',
            'role',
            'role_name',
            'element',
            'element_name',
            'read_permission',
            'read_all_permission',
            'create_permission',
            'update_permission',
            'update_all_permission',
            'delete_permission',
            'delete_all_permission',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TokenSerializer(serializers.Serializer):
    """Сериализатор для токенов."""

    access_token = serializers.CharField(
        help_text='JWT токен для доступа к защищенным эндпоинтам'
    )
    refresh_token = serializers.CharField(
        help_text='JWT токен для обновления access токена'
    )
    expires_in = serializers.IntegerField(
        help_text='Время жизни access токена в секундах'
    )
    token_type = serializers.CharField(
        default='Bearer',
        help_text='Тип токена'
    )

class RefreshTokenSerializer(serializers.Serializer):
    """Сериализатор для обновления токена."""

    refresh_token = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа на запрос логина."""

    message = serializers.CharField(default='Успешный вход')
    user = UserSerializer()
    tokens = TokenSerializer()
