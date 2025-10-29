"""
Management команда для инициализации системы аутентификации и авторизации.

Создает:
- Роли (admin, manager, user, guest)
- Бизнес-элементы (users, products, stores, orders, access_rules)
- Правила доступа для каждой роли
- Тестового администратора
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from server.apps.authentication.models import (
    User,
    Role,
    UserRole,
    BusinessElement,
    AccessRule,
)


class Command(BaseCommand):
    """Команда для инициализации системы."""
    
    help = 'Инициализация системы аутентификации и авторизации'
    
    def handle(self, *args, **options):
        """Выполнение команды."""
        self.stdout.write(self.style.SUCCESS('Начинаем инициализацию...'))
        
        with transaction.atomic():
            # Создаем роли
            roles = self.create_roles()
            self.stdout.write(self.style.SUCCESS(f'Создано ролей: {len(roles)}'))
            
            # Создаем бизнес-элементы
            elements = self.create_business_elements()
            self.stdout.write(self.style.SUCCESS(
                f'Создано бизнес-элементов: {len(elements)}'
            ))
            
            # Создаем правила доступа
            rules_count = self.create_access_rules(roles, elements)
            self.stdout.write(self.style.SUCCESS(
                f'Создано правил доступа: {rules_count}'
            ))
            
            # Создаем тестового администратора
            admin = self.create_admin_user(roles['admin'])
            self.stdout.write(self.style.SUCCESS(
                f'Создан администратор: {admin.email}'
            ))
        
        self.stdout.write(self.style.SUCCESS('Инициализация завершена!'))
    
    def create_roles(self):
        """Создание ролей."""
        roles_data = [
            {
                'name': 'Администратор',
                'code': 'admin',
                'description': 'Полный доступ ко всем ресурсам системы',
            },
            {
                'name': 'Менеджер',
                'code': 'manager',
                'description': 'Управление бизнес-объектами',
            },
            {
                'name': 'Пользователь',
                'code': 'user',
                'description': 'Базовый доступ к системе',
            },
            {
                'name': 'Гость',
                'code': 'guest',
                'description': 'Ограниченный доступ только для чтения',
            },
        ]
        
        roles = {}
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults=role_data,
            )
            roles[role.code] = role
            status = 'создана' if created else 'уже существует'
            self.stdout.write(f'  - Роль "{role.name}" {status}')
        
        return roles
    
    def create_business_elements(self):
        """Создание бизнес-элементов."""
        elements_data = [
            {
                'name': 'Пользователи',
                'code': 'users',
                'description': 'Управление пользователями системы',
            },
            {
                'name': 'Продукты',
                'code': 'products',
                'description': 'Управление продуктами',
            },
            {
                'name': 'Магазины',
                'code': 'stores',
                'description': 'Управление магазинами',
            },
            {
                'name': 'Заказы',
                'code': 'orders',
                'description': 'Управление заказами',
            },
            {
                'name': 'Правила доступа',
                'code': 'access_rules',
                'description': 'Управление правилами доступа',
            },
        ]
        
        elements = {}
        for element_data in elements_data:
            element, created = BusinessElement.objects.get_or_create(
                code=element_data['code'],
                defaults=element_data,
            )
            elements[element.code] = element
            status = 'создан' if created else 'уже существует'
            self.stdout.write(f'  - Элемент "{element.name}" {status}')
        
        return elements
    
    def create_access_rules(self, roles, elements):
        """Создание правил доступа."""
        rules_config = {
            'admin': {
                # Администратор имеет полный доступ ко всему
                'users': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete_all': True,
                },
                'products': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete_all': True,
                },
                'stores': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete_all': True,
                },
                'orders': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete_all': True,
                },
                'access_rules': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete_all': True,
                },
            },
            'manager': {
                # Менеджер может управлять бизнес-объектами
                'users': {
                    'read_all': True,
                },
                'products': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete': True,
                },
                'stores': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete': True,
                },
                'orders': {
                    'read_all': True,
                    'create': True,
                    'update_all': True,
                    'delete': True,
                },
                'access_rules': {
                    'read_all': True,
                },
            },
            'user': {
                # Пользователь может работать только со своими объектами
                'users': {
                    'read': True,  # Может читать свою информацию
                },
                'products': {
                    'read_all': True,  # Может видеть все продукты
                    'create': True,
                    'update': True,  # Только свои
                    'delete': True,  # Только свои
                },
                'stores': {
                    'read_all': True,
                    'create': True,
                    'update': True,
                    'delete': True,
                },
                'orders': {
                    'read': True,  # Только свои заказы
                    'create': True,
                    'update': True,
                    'delete': True,
                },
                'access_rules': {},
            },
            'guest': {
                # Гость может только читать
                'users': {},
                'products': {
                    'read_all': True,
                },
                'stores': {
                    'read_all': True,
                },
                'orders': {},
                'access_rules': {},
            },
        }
        
        rules_count = 0
        for role_code, role_rules in rules_config.items():
            role = roles[role_code]
            
            for element_code, permissions in role_rules.items():
                element = elements[element_code]
                
                rule, created = AccessRule.objects.get_or_create(
                    role=role,
                    element=element,
                    defaults={
                        'read_permission': permissions.get('read', False),
                        'read_all_permission': permissions.get('read_all', False),
                        'create_permission': permissions.get('create', False),
                        'update_permission': permissions.get('update', False),
                        'update_all_permission': permissions.get('update_all', False),
                        'delete_permission': permissions.get('delete', False),
                        'delete_all_permission': permissions.get('delete_all', False),
                    },
                )
                
                if not created:
                    # Обновляем существующее правило
                    rule.read_permission = permissions.get('read', False)
                    rule.read_all_permission = permissions.get('read_all', False)
                    rule.create_permission = permissions.get('create', False)
                    rule.update_permission = permissions.get('update', False)
                    rule.update_all_permission = permissions.get('update_all', False)
                    rule.delete_permission = permissions.get('delete', False)
                    rule.delete_all_permission = permissions.get('delete_all', False)
                    rule.save()
                
                rules_count += 1
                status = 'создано' if created else 'обновлено'
                self.stdout.write(
                    f'  - Правило {role.name} -> {element.name} {status}'
                )
        
        return rules_count
    
    def create_admin_user(self, admin_role):
        """Создание тестового администратора."""
        email = 'admin@example.com'
        password = 'Admin123!'
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        
        if created:
            user.set_password(password)
            user.save()
            
            # Назначаем роль администратора
            UserRole.objects.create(user=user, role=admin_role)
            
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Пароль: {password}')
        else:
            self.stdout.write('  Администратор уже существует')
        
        return user
