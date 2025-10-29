"""
Модели для системы аутентификации и авторизации.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя."""

    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя."""
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя.
    Использует email вместо username для аутентификации.
    """

    email = models.EmailField(
        'Email адрес',
        unique=True,
        db_index=True,
    )
    first_name = models.CharField('Имя', max_length=150, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    middle_name = models.CharField('Отчество', max_length=150, blank=True)

    is_active = models.BooleanField(
        'Активный',
        default=True,
        help_text='Указывает, активен ли пользователь. Отключите вместо удаления.',
    )
    is_staff = models.BooleanField(
        'Статус персонала',
        default=False,
        help_text='Указывает, может ли пользователь входить в админ-панель.',
    )

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    # Переопределяем поля из PermissionsMixin для избежания конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Группы',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Права пользователя',
        blank=True,
        help_text='Конкретные права этого пользователя.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )


    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        """Строковое представление пользователя."""
        return self.email

    def get_full_name(self):
        """Возвращает полное имя пользователя."""
        full_name = f'{self.last_name} {self.first_name} {self.middle_name}'.strip()
        return full_name or self.email


class Role(models.Model):
    """Модель роли в системе."""

    name = models.CharField('Название', max_length=100, unique=True)
    code = models.CharField(
        'Код',
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Уникальный код роли (admin, manager, user, guest)',
    )
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']

    def __str__(self):
        """Строковое представление роли."""
        return self.name


class UserRole(models.Model):
    """Связь пользователей и ролей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Пользователь',
        db_index=True,
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='Роль',
        db_index=True,
    )
    assigned_at = models.DateTimeField('Дата назначения', auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name='Назначил',
    )

    class Meta:
        db_table = 'user_roles'
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role'],
                name='unique_user_role'
            )
        ]

    def __str__(self):
        """Строковое представление связи."""
        return f'{self.user.email} - {self.role.name}'


class BusinessElement(models.Model):
    """Модель бизнес-объекта приложения."""

    name = models.CharField('Название', max_length=100, unique=True)
    code = models.CharField(
        'Код',
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Уникальный код элемента (users, products, stores, orders, access_rules)',
    )
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'business_elements'
        verbose_name = 'Бизнес-элемент'
        verbose_name_plural = 'Бизнес-элементы'
        ordering = ['name']

    def __str__(self):
        """Строковое представление элемента."""
        return self.name


class AccessRule(models.Model):
    """Правило доступа роли к бизнес-элементу."""

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='access_rules',
        verbose_name='Роль',
        db_index=True,
    )
    element = models.ForeignKey(
        BusinessElement,
        on_delete=models.CASCADE,
        related_name='access_rules',
        verbose_name='Бизнес-элемент',
        db_index=True,
    )

    # Права доступа
    read_permission = models.BooleanField(
        'Чтение своих объектов',
        default=False,
        help_text='Может читать объекты, которые создал сам',
    )
    read_all_permission = models.BooleanField(
        'Чтение всех объектов',
        default=False,
        help_text='Может читать все объекты',
    )
    create_permission = models.BooleanField(
        'Создание',
        default=False,
        help_text='Может создавать новые объекты',
    )
    update_permission = models.BooleanField(
        'Обновление своих объектов',
        default=False,
        help_text='Может обновлять объекты, которые создал сам',
    )
    update_all_permission = models.BooleanField(
        'Обновление всех объектов',
        default=False,
        help_text='Может обновлять все объекты',
    )
    delete_permission = models.BooleanField(
        'Удаление своих объектов',
        default=False,
        help_text='Может удалять объекты, которые создал сам',
    )
    delete_all_permission = models.BooleanField(
        'Удаление всех объектов',
        default=False,
        help_text='Может удалять все объекты',
    )

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        db_table = 'access_rules'
        verbose_name = 'Правило доступа'
        verbose_name_plural = 'Правила доступа'
        ordering = ['role', 'element']
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'element'],
                name='unique_role_element'
            )
        ]

    def __str__(self):
        """Строковое представление правила."""
        return f'{self.role.name} -> {self.element.name}'


class Session(models.Model):
    """Модель сессии пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Пользователь',
        db_index=True,
    )
    token_hash = models.CharField(
        'Хеш токена',
        max_length=255,
        db_index=True,
        help_text='SHA-256 хеш access токена',
    )
    refresh_token_hash = models.CharField(
        'Хеш refresh токена',
        max_length=255,
        db_index=True,
        help_text='SHA-256 хеш refresh токена',
    )
    expires_at = models.DateTimeField('Истекает', db_index=True)
    refresh_expires_at = models.DateTimeField('Refresh истекает')

    ip_address = models.GenericIPAddressField(
        'IP адрес',
        null=True,
        blank=True,
    )
    user_agent = models.TextField('User Agent', blank=True)

    is_active = models.BooleanField('Активна', default=True, db_index=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        db_table = 'sessions'
        verbose_name = 'Сессия'
        verbose_name_plural = 'Сессии'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token_hash', 'is_active']),
        ]

    def __str__(self):
        """Строковое представление сессии."""
        return f'{self.user.email} - {self.created_at}'

    def is_expired(self):
        """Проверка, истек ли access token."""
        return timezone.now() > self.expires_at

    def is_refresh_expired(self):
        """Проверка, истек ли refresh token."""
        return timezone.now() > self.refresh_expires_at
