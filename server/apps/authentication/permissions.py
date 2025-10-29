"""
Permissions для проверки прав доступа к ресурсам.
"""
from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist

from .models import AccessRule, BusinessElement


class IsAuthenticated(permissions.BasePermission):
    """Проверка, что пользователь аутентифицирован."""
    
    message = 'Требуется аутентификация'
    
    def has_permission(self, request, view):
        """Проверка прав на уровне представления."""
        return bool(request.user and request.user.is_authenticated)


class HasResourcePermission(permissions.BasePermission):
    """
    Проверка прав доступа к ресурсу на основе системы access_rules.
    
    Атрибуты view:
        resource_code (str): код бизнес-элемента (например, 'products')
        owner_field (str): название поля владельца объекта (по умолчанию 'owner')
    """
    
    def has_permission(self, request, view):
        """Проверка прав на уровне представления."""
        # Проверяем аутентификацию
        if not request.user or not request.user.is_authenticated:
            self.message = 'Требуется аутентификация'
            return False
        
        # Получаем код ресурса из view
        resource_code = getattr(view, 'resource_code', None)
        if not resource_code:
            # Если не указан resource_code, разрешаем доступ
            # (можно изменить на запрет по умолчанию)
            return True
        
        # Определяем требуемое право в зависимости от метода
        method_permissions = {
            'GET': ('read_all_permission', 'read_permission'),
            'POST': ('create_permission',),
            'PUT': ('update_all_permission', 'update_permission'),
            'PATCH': ('update_all_permission', 'update_permission'),
            'DELETE': ('delete_all_permission', 'delete_permission'),
        }
        
        required_permissions = method_permissions.get(request.method, ())
        if not required_permissions:
            return True
        
        # Получаем все роли пользователя
        user_roles = request.user.user_roles.select_related('role').all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            self.message = 'У пользователя нет ролей'
            return False
        
        # Получаем бизнес-элемент
        try:
            element = BusinessElement.objects.get(code=resource_code)
        except ObjectDoesNotExist:
            self.message = f'Ресурс {resource_code} не найден'
            return False
        
        # Получаем правила доступа для ролей пользователя
        access_rules = AccessRule.objects.filter(
            role_id__in=role_ids,
            element=element,
        )
        
        # Проверяем наличие хотя бы одного подходящего права
        for rule in access_rules:
            for perm in required_permissions:
                if getattr(rule, perm, False):
                    # Сохраняем информацию о правах для has_object_permission
                    request.access_rules = access_rules
                    request.resource_element = element
                    return True
        
        self.message = 'Недостаточно прав для выполнения операции'
        return False
    
    def has_object_permission(self, request, view, obj):
        """Проверка прав на уровне объекта."""
        # Для GET списка не проверяем объект
        if request.method == 'GET' and not hasattr(view, 'get_object'):
            return True
        
        # Получаем правила доступа из request (установлены в has_permission)
        access_rules = getattr(request, 'access_rules', None)
        if not access_rules:
            return False
        
        # Определяем права для проверки владельца
        method_owner_permissions = {
            'GET': ('read_permission', 'read_all_permission'),
            'PUT': ('update_permission', 'update_all_permission'),
            'PATCH': ('update_permission', 'update_all_permission'),
            'DELETE': ('delete_permission', 'delete_all_permission'),
        }
        
        owner_permissions = method_owner_permissions.get(request.method, ())
        if not owner_permissions:
            return True
        
        # Получаем поле владельца
        owner_field = getattr(view, 'owner_field', 'owner')
        
        # Проверяем, является ли пользователь владельцем объекта
        is_owner = False
        if hasattr(obj, owner_field):
            owner = getattr(obj, owner_field)
            # Владелец может быть объектом User или просто ID
            if hasattr(owner, 'id'):
                is_owner = owner.id == request.user.id
            else:
                is_owner = owner == request.user.id
        
        # Проверяем права
        for rule in access_rules:
            # Если пользователь владелец, проверяем "обычные" права
            if is_owner and getattr(rule, owner_permissions[0], False):
                return True
            # Проверяем "все" права
            if getattr(rule, owner_permissions[1], False):
                return True
        
        self.message = 'Недостаточно прав для доступа к объекту'
        return False


class IsAdminRole(permissions.BasePermission):
    """Проверка, что пользователь имеет роль администратора."""
    
    message = 'Требуются права администратора'
    
    def has_permission(self, request, view):
        """Проверка прав на уровне представления."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Проверяем наличие роли admin
        return request.user.user_roles.filter(role__code='admin').exists()
