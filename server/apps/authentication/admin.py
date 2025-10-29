"""
Административный интерфейс для моделей аутентификации и авторизации.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Role, UserRole, BusinessElement, AccessRule, Session


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ для модели User."""
    
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'middle_name'),
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Админ для модели Role."""
    
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Админ для модели UserRole."""
    
    list_display = ['user', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__email', 'role__name']
    raw_id_fields = ['user', 'assigned_by']
    readonly_fields = ['assigned_at']


@admin.register(BusinessElement)
class BusinessElementAdmin(admin.ModelAdmin):
    """Админ для модели BusinessElement."""
    
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']


@admin.register(AccessRule)
class AccessRuleAdmin(admin.ModelAdmin):
    """Админ для модели AccessRule."""
    
    list_display = [
        'role',
        'element',
        'read_permission',
        'read_all_permission',
        'create_permission',
        'update_permission',
        'update_all_permission',
        'delete_permission',
        'delete_all_permission',
    ]
    list_filter = ['role', 'element']
    search_fields = ['role__name', 'element__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основное', {
            'fields': ('role', 'element'),
        }),
        ('Права чтения', {
            'fields': ('read_permission', 'read_all_permission'),
        }),
        ('Права создания', {
            'fields': ('create_permission',),
        }),
        ('Права обновления', {
            'fields': ('update_permission', 'update_all_permission'),
        }),
        ('Права удаления', {
            'fields': ('delete_permission', 'delete_all_permission'),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Админ для модели Session."""
    
    list_display = ['user', 'is_active', 'expires_at', 'ip_address', 'created_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['token_hash', 'refresh_token_hash', 'created_at']
    raw_id_fields = ['user']
    
    def has_add_permission(self, request):
        """Запрещаем создание сессий через админку."""
        return False
