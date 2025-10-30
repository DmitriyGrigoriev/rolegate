# Инструкция по использованию системы аутентификации

## Использование API

### Аутентификация
- `POST /api/auth/register/` - регистрация
- `POST /api/auth/login/` - вход
- `POST /api/auth/logout/` - выход
- `POST /api/auth/refresh/` - обновление токена
- `GET /api/auth/me/` - текущий пользователь
- `PUT /api/auth/me/` - обновление профиля
- `DELETE /api/auth/me/` - удаление аккаунта

### Управление (только администраторы)
- `GET/POST /api/users/` - пользователи
- `GET/PUT/DELETE /api/users/{id}/` - пользователь
- `POST /api/users/{id}/assign-role/` - назначить роль
- `DELETE /api/users/{id}/roles/{role_id}/` - отозвать роль
- `GET/POST /api/roles/` - роли
- `GET/POST /api/access-rules/` - правила доступа

### Mock API (демонстрация)
- `GET/POST /api/mock/products/` - продукты
- `GET/PUT/DELETE /api/mock/products/{id}/` - продукт
- `GET/POST /api/mock/stores/` - магазины
- `GET/POST /api/mock/orders/` - заказы

### Регистрация

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович"
  }'
```

### Вход

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

Ответ:
```json
{
  "message": "Успешный вход",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Администратор",
    "last_name": "Системы",
    "full_name": "Системы Администратор",
    "is_active": true,
    "roles": [
      {
        "id": 1,
        "name": "Администратор",
        "code": "admin"
      }
    ],
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_in": 900,
    "token_type": "Bearer"
  }
}
```

### Получение информации о текущем пользователе

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Обновление профиля

```bash
curl -X PUT http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Петр",
    "last_name": "Петров"
  }'
```

### Обновление токена

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Выход

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Удаление аккаунта

```bash
curl -X DELETE http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Управление правами (только для администраторов)

### Список пользователей

```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Список ролей

```bash
curl -X GET http://localhost:8000/api/roles/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Назначить роль пользователю

```bash
curl -X POST http://localhost:8000/api/users/2/assign-role/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_id": 2
  }'
```

### Отозвать роль

```bash
curl -X DELETE http://localhost:8000/api/users/2/roles/2/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Список правил доступа

```bash
curl -X GET http://localhost:8000/api/access-rules/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Создать правило доступа

```bash
curl -X POST http://localhost:8000/api/access-rules/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": 2,
    "element": 1,
    "read_permission": true,
    "read_all_permission": false,
    "create_permission": true,
    "update_permission": true,
    "update_all_permission": false,
    "delete_permission": false,
    "delete_all_permission": false
  }'
```

### Обновить правило доступа

```bash
curl -X PUT http://localhost:8000/api/access-rules/1/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": 2,
    "element": 1,
    "read_permission": true,
    "read_all_permission": true,
    "create_permission": true,
    "update_permission": true,
    "update_all_permission": true,
    "delete_permission": true,
    "delete_all_permission": false
  }'
```

## Mock API для демонстрации авторизации

Система включает Mock ViewSets для демонстрации работы авторизации без реальной БД.

### Продукты

```bash
# Список продуктов (требует права read_all_permission для products)
curl -X GET http://localhost:8000/api/mock/products/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Детальная информация (проверяет права на объект)
curl -X GET http://localhost:8000/api/mock/products/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Создание продукта (требует create_permission)
curl -X POST http://localhost:8000/api/mock/products/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Новый продукт",
    "price": 1000
  }'

# Обновление продукта (требует update_permission или update_all_permission)
curl -X PUT http://localhost:8000/api/mock/products/1/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Обновленный продукт",
    "price": 1500
  }'

# Удаление продукта (требует delete_permission или delete_all_permission)
curl -X DELETE http://localhost:8000/api/mock/products/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Магазины

```bash
curl -X GET http://localhost:8000/api/mock/stores/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Заказы

```bash
curl -X GET http://localhost:8000/api/mock/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Коды ошибок

- **400 Bad Request** - неверные данные запроса
- **401 Unauthorized** - пользователь не аутентифицирован
- **403 Forbidden** - пользователь не имеет прав на операцию
- **404 Not Found** - ресурс не найден

## Примеры ответов с ошибками

### 401 Unauthorized

```json
{
  "detail": "Требуется аутентификация"
}
```

### 403 Forbidden

```json
{
  "detail": "Недостаточно прав для выполнения операции"
}
```

## Тестирование

Для тестирования системы можно использовать созданного администратора:
- Email: `admin@example.com`
- Пароль: `Admin123!`

Администратор имеет полный доступ ко всем ресурсам.

Можно создать пользователей с разными ролями и проверить работу системы прав доступа.

## Структура проекта

```
server/apps/authentication/
├── __init__.py
├── apps.py                  # Конфигурация приложения
├── models.py                # Модели БД
├── serializers.py           # Сериализаторы DRF
├── views.py                 # API views
├── mock_views.py            # Mock views для демонстрации
├── permissions.py           # Классы проверки прав
├── middleware.py            # JWT middleware
├── utils.py                 # Утилиты (JWT, хеширование)
├── urls.py                  # URL конфигурация
└── management/
    └── commands/
        └── init_auth_system.py  # Команда инициализации
```
## Расширение системы

Для добавления новых бизнес-объектов:

1. Создайте модель с полем `owner` (ForeignKey на User)
2. Создайте ViewSet с `permission_classes = [IsAuthenticated, HasResourcePermission]`
3. Укажите `resource_code` в ViewSet (код из BusinessElement)
4. Создайте BusinessElement и AccessRule в БД
5. Назначьте права ролям через API или админку
