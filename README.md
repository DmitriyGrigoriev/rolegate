# Доступ на основе ролей - rolegate


Этот проект был создан с помощью [`wemake-django-template`](https://github.com/wemake-services/wemake-django-template). Текущая версия шаблона: [3b6ab46](https://github.com/wemake-services/wemake-django-template/tree/3b6ab4692b7436ed9255ed7521bd204b41f118f5). Последнии обновления [updated](https://github.com/wemake-services/wemake-django-template/compare/3b6ab4692b7436ed9255ed7521bd204b41f118f5...master)


[![wemake.services](https://img.shields.io/badge/%20-wemake.services-green.svg?label=%20&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC%2FxhBQAAAAFzUkdCAK7OHOkAAAAbUExURQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP%2F%2F%2F5TvxDIAAAAIdFJOUwAjRA8xXANAL%2Bv0SAAAADNJREFUGNNjYCAIOJjRBdBFWMkVQeGzcHAwksJnAPPZGOGAASzPzAEHEGVsLExQwE7YswCb7AFZSF3bbAAAAABJRU5ErkJggg%3D%3D)](https://wemake-services.github.io)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)


## Предварительные требования

Вам понадобится:

- `python3.11` (see `pyproject.toml` for exact version), use `pyenv install`
- `postgresql` (see `docker-compose.yml` for exact version)
- Latest `docker`


## Разработка

При локальной разработке используется:
- [`poetry`](https://github.com/python-poetry/poetry) (**required**)
- [`pyenv`](https://github.com/pyenv/pyenv)



### Архитектура

Проект реализует собственную систему аутентификации и авторизации на основе ролей с гранулярным управлением правами доступа.

Проект реализует трехуровневую модель безопасности:

1. **Аутентификация** — определение личности пользователя
2. **Идентификация** — связывание запроса с пользователем
3. **Авторизация** — проверка прав доступа к ресурсам

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request + JWT Token
       ↓
┌─────────────────────────────────────┐
│     Authentication Middleware       │
│  • Извлечение токена из заголовка   │
│  • Валидация JWT                    │
│  • Проверка сессии в БД             │
│  • Установка request.user           │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│     Authorization Middleware        │
│  • Определение запрашиваемого       │
│    ресурса (business_element)       │
│  • Загрузка ролей пользователя      │
│  • Проверка access_rules            │
│  • Определение владельца объекта    │
└──────┬──────────────────────────────┘
       │
       ↓ (если права есть)
┌─────────────────────────────────────┐
│            View / API               │
└─────────────────────────────────────┘
```

### Структура базы данных

#### 1. Модуль аутентификации

```python
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
```

**`users`** — Пользователи системы
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- bcrypt hash
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    middle_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,  -- для мягкого удаления
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**`sessions`** — Активные сессии пользователей
```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,              -- JWT токен
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,   -- для инвалидации токена
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Принцип работы аутентификации:**
- При login создается JWT токен содержащий `user_id` и `exp` (время истечения)
- Токен сохраняется в таблице `sessions`
- Клиент отправляет токен в заголовке: `Authorization: Bearer {token}`
- Middleware проверяет:
  1. Валидность JWT (подпись, срок действия)
  2. Наличие активной сессии в БД
  3. `is_active=True` для пользователя
- При logout сессия помечается как `is_active=False`

#### 2. Модуль авторизации (RBAC)

**`roles`** — Роли в системе
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,  -- admin, manager, user, guest
    description TEXT
);
```

**Предустановленные роли:**
- `admin` — полный доступ ко всем ресурсам и управлению системой
- `manager` — управление бизнес-объектами (товары, магазины, заказы)
- `user` — доступ к своим объектам
- `guest` — только чтение публичных данных

**`user_roles`** — Связь пользователей и ролей (many-to-many)
```sql
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);
```

**`business_elements`** — Ресурсы приложения
```sql
CREATE TABLE business_elements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,  -- users, products, stores, orders, access_rules
    description TEXT
);
```

**Бизнес-элементы системы:**
- `users` — управление пользователями
- `products` — товары
- `stores` — магазины
- `orders` — заказы
- `access_rules` — правила доступа (мета-уровень)

**`access_rules`** — Правила доступа роли к ресурсу
```sql
CREATE TABLE access_rules (
    id SERIAL PRIMARY KEY,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    element_id INTEGER REFERENCES business_elements(id) ON DELETE CASCADE,

    -- Права на чтение
    read_permission BOOLEAN DEFAULT FALSE,      -- чтение своих объектов
    read_all_permission BOOLEAN DEFAULT FALSE,  -- чтение всех объектов

    -- Права на создание
    create_permission BOOLEAN DEFAULT FALSE,

    -- Права на обновление
    update_permission BOOLEAN DEFAULT FALSE,     -- обновление своих
    update_all_permission BOOLEAN DEFAULT FALSE, -- обновление всех

    -- Права на удаление
    delete_permission BOOLEAN DEFAULT FALSE,     -- удаление своих
    delete_all_permission BOOLEAN DEFAULT FALSE, -- удаление всех

    UNIQUE(role_id, element_id)
);
```

#### 3. Бизнес-объекты (примеры для демонстрации)

Все бизнес-объекты имеют поле `owner_id` для разграничения доступа:

**Пример: `products`** (mock-реализация)
```python
{
    "id": 1,
    "name": "Товар 1",
    "price": 100.00,
    "owner_id": 5,  # ID пользователя-создателя
    "created_at": "2024-01-15T10:00:00Z"
}
```

### Логика проверки прав доступа

#### Алгоритм авторизации

Система авторизации реализована через **DRF Permission Classes** (`server/apps/authentication/permissions.py`), которые автоматически применяются на каждый HTTP запрос к защищенным endpoints.

---

##### 1. IsAuthenticated - Базовая проверка аутентификации

```python
class IsAuthenticated(permissions.BasePermission):
    """
    Первый уровень защиты: проверка наличия аутентифицированного пользователя.

    Применяется ко всем защищенным endpoints перед проверкой прав.
    """

    message = 'Требуется аутентификация'

    def has_permission(self, request, view):
        """
        Проверка:
        - request.user существует (установлен JWTAuthentication)
        - request.user.is_authenticated == True

        Returns:
            True - если пользователь аутентифицирован
            False - возвращает 401 Unauthorized
        """
        return bool(request.user and request.user.is_authenticated)
```

**Когда вызывается:**
- Автоматически для всех views с `permission_classes = [IsAuthenticated, ...]`
- Выполняется **до** `has_object_permission()`
- Если False → запрос останавливается с кодом **401**

**Пример использования:**
```python
class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """GET /api/auth/me/ - только для аутентифицированных"""
        return Response(UserSerializer(request.user).data)
```

---

##### 2. HasResourcePermission - Проверка прав на основе RBAC

Это **ядро системы авторизации**, которое реализует логику проверки прав доступа на основе таблиц `access_rules`.

```python
class HasResourcePermission(permissions.BasePermission):
    """
    Проверка прав доступа к ресурсу с учетом:
    - Ролей пользователя (user_roles)
    - Правил доступа (access_rules)
    - Владельца объекта (owner_id)

    Требует атрибутов в ViewSet:
        resource_code: 'products' | 'stores' | 'orders' | ...
        owner_field: 'owner' | 'created_by' | 'user' | ...
    """
```

##### 2.1. Проверка на уровне коллекции (has_permission)

Вызывается для операций со **списками** или **созданием** объектов:
- `GET /api/mock/products/` (list)
- `POST /api/mock/products/` (create)

```python
def has_permission(self, request, view):
    """
    Проверка прав без конкретного объекта.

    Алгоритм:
    ┌─────────────────────────────────────────────────┐
    │ 1. Проверка аутентификации                      │
    │    request.user.is_authenticated?               │
    │    ├─ False → 401 Unauthorized                  │
    │    └─ True → продолжаем                         │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 2. Получение resource_code из ViewSet           │
    │    resource_code = view.resource_code           │
    │    Пример: 'products', 'stores', 'orders'       │
    │    ├─ Не указан → True (доступ разрешен)        │
    │    └─ Указан → продолжаем                       │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 3. Определение требуемых прав из HTTP метода    │
    │    GET    → read_all_permission | read_permission │
    │    POST   → create_permission                   │
    │    PUT    → update_all_permission | update_permission │
    │    PATCH  → update_all_permission | update_permission │
    │    DELETE → delete_all_permission | delete_permission │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 4. Загрузка ролей пользователя                  │
    │    user_roles = request.user.user_roles.all()   │
    │    role_ids = [ur.role_id for ur in user_roles] │
    │    ├─ Нет ролей → False (403)                   │
    │    └─ Есть роли → продолжаем                    │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 5. Получение бизнес-элемента                    │
    │    element = BusinessElement.objects.get(       │
    │       code=resource_code                        │
    │    )                                            │
    │    ├─ Не найден → False (403)                   │
    │    └─ Найден → продолжаем                       │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 6. Загрузка правил доступа                      │
    │    access_rules = AccessRule.objects.filter(    │
    │       role_id__in=role_ids,                     │
    │       element=element                           │
    │    )                                            │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 7. Проверка наличия требуемого права            │
    │    for rule in access_rules:                    │
    │        for perm in required_permissions:        │
    │            if getattr(rule, perm) == True:      │
    │                ✓ Доступ разрешен                │
    │    ├─ Нет подходящих прав → False (403)         │
    │    └─ Есть право → True, сохраняем в request    │
    └─────────────────────────────────────────────────┘
    """

    # 1. Проверка аутентификации
    if not request.user or not request.user.is_authenticated:
        self.message = 'Требуется аутентификация'
        return False

    # 2. Получение resource_code
    resource_code = getattr(view, 'resource_code', None)
    if not resource_code:
        return True  # Нет resource_code = нет проверки

    # 3. Маппинг HTTP методов на права
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

    # 4. Загрузка ролей пользователя
    user_roles = request.user.user_roles.select_related('role').all()
    role_ids = [ur.role_id for ur in user_roles]

    if not role_ids:
        self.message = 'У пользователя нет ролей'
        return False

    # 5. Получение бизнес-элемента
    try:
        element = BusinessElement.objects.get(code=resource_code)
    except ObjectDoesNotExist:
        self.message = f'Ресурс {resource_code} не найден'
        return False

    # 6. Загрузка правил доступа
    access_rules = AccessRule.objects.filter(
        role_id__in=role_ids,
        element=element,
    )

    # 7. Проверка наличия требуемого права
    for rule in access_rules:
        for perm in required_permissions:
            if getattr(rule, perm, False):
                # Сохраняем правила в request для has_object_permission
                request.access_rules = access_rules
                request.resource_element = element
                return True

    self.message = 'Недостаточно прав для выполнения операции'
    return False
```

**Важные моменты:**

1. **Tuple разрешений для GET/UPDATE/DELETE:**
   ```python
   'GET': ('read_all_permission', 'read_permission')
   ```
   - Проверяются **оба** права
   - Достаточно иметь **любое** из них
   - `read_all_permission` → видит все объекты
   - `read_permission` → видит только свои (проверка в `has_object_permission`)

2. **Кеширование правил в request:**
   ```python
   request.access_rules = access_rules
   request.resource_element = element
   ```
   - Избегаем повторных SQL запросов в `has_object_permission()`
   - Правила уже загружены для конкретного ресурса и ролей

3. **Select related оптимизация:**
   ```python
   user_roles = request.user.user_roles.select_related('role').all()
   ```
   - Загружает роли за 1 SQL запрос вместо N запросов
   - Но на практике роли уже загружены через prefetch в `JWTAuthentication`

---

##### 2.2. Проверка на уровне объекта (has_object_permission)

Вызывается для операций с **конкретным** объектом:
- `GET /api/mock/products/5/` (retrieve)
- `PUT /api/mock/products/5/` (update)
- `DELETE /api/mock/products/5/` (destroy)

```python
def has_object_permission(self, request, view, obj):
    """
    Проверка прав с учетом владельца объекта.

    Алгоритм:
    ┌─────────────────────────────────────────────────┐
    │ 1. Получение сохраненных правил из request      │
    │    access_rules = request.access_rules          │
    │    (установлены в has_permission)               │
    │    ├─ Не найдены → False (403)                  │
    │    └─ Найдены → продолжаем                      │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌───────────────────────────────────────────────────────┐
    │ 2. Определение прав для проверки владельца            │
    │    GET    → read_permission | read_all_permission     │
    │    PUT    → update_permission | update_all_permission │
    │    PATCH  → update_permission | update_all_permission │
    │    DELETE → delete_permission | delete_all_permission │
    └─────────────────┬─────────────────────────────────────┘
                      │
                      ↓
    ┌───────────────────────────────────────────────────────┐
    │ 3. Получение поля владельца из ViewSet                │
    │    owner_field = view.owner_field (default: 'owner')  │
    │    Примеры:                                           │
    │    - obj.owner → ID владельца                         │
    │    - obj.created_by → User объект                     │
    │    - obj.user_id → внешний ключ                       │
    └─────────────────┬─────────────────────────────────────┘
                      │
                      ↓
    ┌───────────────────────────────────────────────────┐
    │ 4. Проверка, является ли пользователь владельцем  │
    │    owner = getattr(obj, owner_field)              │
    │    if hasattr(owner, 'id'):                       │
    │        is_owner = owner.id == request.user.id     │
    │    else:                                          │
    │        is_owner = owner == request.user.id        │
    └─────────────────┬─────────────────────────────────┘
                      │
                      ↓
    ┌───────────────────────────────────────────────────┐
    │ 5. Проверка прав в правилах доступа               │
    │    for rule in access_rules:                      │
    │        # Вариант 1: Пользователь владелец         │
    │        if is_owner and rule.{action}_permission:  │
    │            ✓ Доступ разрешен                      │
    │                                                   │
    │        # Вариант 2: Права на все объекты          │
    │        if rule.{action}_all_permission:           │
    │            ✓ Доступ разрешен                      │
    │                                                   │
    │    ├─ Ни одно правило не подошло → False (403)    │
    │    └─ Есть подходящее правило → True              │
    └───────────────────────────────────────────────────┘
    """

    # 1. Получение правил из request
    access_rules = getattr(request, 'access_rules', None)
    if not access_rules:
        return False

    # 2. Маппинг методов на права владельца
    method_owner_permissions = {
        'GET': ('read_permission', 'read_all_permission'),
        'PUT': ('update_permission', 'update_all_permission'),
        'PATCH': ('update_permission', 'update_all_permission'),
        'DELETE': ('delete_permission', 'delete_all_permission'),
    }

    owner_permissions = method_owner_permissions.get(request.method, ())
    if not owner_permissions:
        return True

    # 3. Получение поля владельца
    owner_field = getattr(view, 'owner_field', 'owner')

    # 4. Проверка владельца объекта
    is_owner = False
    if hasattr(obj, owner_field):
        owner = getattr(obj, owner_field)
        # Владелец может быть объектом User или просто ID
        if hasattr(owner, 'id'):
            is_owner = owner.id == request.user.id
        else:
            is_owner = owner == request.user.id

    # 5. Проверка прав
    for rule in access_rules:
        # Если владелец - проверяем "обычное" право
        if is_owner and getattr(rule, owner_permissions[0], False):
            return True

        # Проверяем "все" право
        if getattr(rule, owner_permissions[1], False):
            return True

    self.message = 'Недостаточно прав для доступа к объекту'
    return False
```

**Логика проверки владельца:**

```python
# Пример 1: owner - это ID (int)
class MockProduct:
    id = 5
    name = 'Ноутбук'
    owner = 123  # ID пользователя

# Проверка:
is_owner = obj.owner == request.user.id  # 123 == 123 → True

# Пример 2: owner - это ForeignKey (User объект)
class Product(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

# Проверка:
is_owner = obj.owner.id == request.user.id
```

**Примеры сценариев:**

| HTTP запрос           | Права в access_rules                                      | is_owner | Результат                                  |
|-----------------------|-----------------------------------------------------------|----------|--------------------------------------------|
| `GET /products/5/`    | `read_permission=True`<br>`read_all_permission=False`     | ✓ Да     | **200** Доступ разрешен                    |
| `GET /products/5/`    | `read_permission=True`<br>`read_all_permission=False`     | ✗ Нет    | **403** Недостаточно прав                  |
| `GET /products/5/`    | `read_permission=False`<br>`read_all_permission=True`     | ✗ Нет    | **200** Доступ разрешен (может читать все) |
| `DELETE /products/5/` | `delete_permission=True`<br>`delete_all_permission=False` | ✓ Да     | **200** Удалено                            |
| `DELETE /products/5/` | `delete_permission=True`<br>`delete_all_permission=False` | ✗ Нет    | **403** Нельзя удалить чужой объект        |

---

##### 3. IsAdminRole - Проверка административных прав

Используется для защиты административных endpoints (управление пользователями, ролями, правами доступа).

```python
class IsAdminRole(permissions.BasePermission):
    """
    Проверяет наличие роли 'admin' у пользователя.

    Применяется к ViewSet'ам:
    - UserViewSet (управление пользователями)
    - RoleViewSet (управление ролями)
    - BusinessElementViewSet (управление бизнес-элементами)
    - AccessRuleViewSet (управление правилами доступа)
    """

    message = 'Требуются права администратора'

    def has_permission(self, request, view):
        """
        Алгоритм:
        1. Проверка аутентификации
        2. Проверка наличия роли с кодом 'admin'

        SQL запрос:
        SELECT 1 FROM user_roles
        JOIN roles ON user_roles.role_id = roles.id
        WHERE user_roles.user_id = {request.user.id}
          AND roles.code = 'admin'
        LIMIT 1
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем наличие роли admin
        return request.user.user_roles.filter(role__code='admin').exists()
```

**Использование:**

```python
class UserViewSet(viewsets.ModelViewSet):
    """
    API для управления пользователями.
    Доступ только для администраторов.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Оба permission должны быть True
    permission_classes = [IsAuthenticated, IsAdminRole]

    # Endpoints:
    # GET    /api/users/           - список всех пользователей
    # POST   /api/users/           - создание пользователя
    # GET    /api/users/{id}/      - конкретный пользователь
    # PUT    /api/users/{id}/      - обновление пользователя
    # DELETE /api/users/{id}/      - удаление пользователя
```
---

#### Порядок выполнения проверок

```
          HTTP Request → DRF View
                      │
    ┌─────────────────────────────────────────────────┐
    │ Permission Classes выполняются в порядке        │
    │ объявления в permission_classes                 │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 1. IsAuthenticated.has_permission()             │
    │    ├─ False → 401 Unauthorized (остановка)      │
    │    └─ True → переход к следующему permission    │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 2. HasResourcePermission.has_permission()       │
    │    ├─ False → 403 Forbidden (остановка)         │
    │    └─ True → выполнение View метода             │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓
    ┌─────────────────────────────────────────────────┐
    │ 3. View.get_object() / View.list() / etc.       │
    │    Выполнение бизнес-логики                     │
    └─────────────────┬───────────────────────────────┘
                      │
                      ↓ (только для retrieve/update/delete)
    ┌─────────────────────────────────────────────────┐
    │ 4. HasResourcePermission.has_object_permission()│
    │    ├─ False → 403 Forbidden                     │
    │    └─ True → Response                           │
    └─────────────────────────────────────────────────┘
```

**Важно:** `has_object_permission()` вызывается **после** `has_permission()` и **только** для методов, работающих с конкретным объектом:
- `retrieve()` (GET /resource/{id}/)
- `update()` (PUT /resource/{id}/)
- `partial_update()` (PATCH /resource/{id}/)
- `destroy()` (DELETE /resource/{id}/)

Для `list()` и `create()` вызывается только `has_permission()`.

---

#### Примеры сценариев с полным циклом

##### Сценарий 1: Просмотр списка продуктов (роль "user")

```python
# Запрос
GET /api/mock/products/
Authorization: Bearer eyJhbGc...

# Роль пользователя: "user"
# Правила доступа:
AccessRule(
    role=Role(code='user'),
    element=BusinessElement(code='products'),
    read_permission=True,           # ✓
    read_all_permission=False,      # ✗
)

# Выполнение:
┌─ IsAuthenticated.has_permission() ──────────┐
│  request.user.is_authenticated? → True  ✓   │
└─────────────────────────────────────────────┘
         ↓
┌─ HasResourcePermission.has_permission() ────┐
│  resource_code = 'products'                 │
│  required_permissions = ('read_all_permission', 'read_permission')
│  access_rules.filter(element='products')    │
│  → rule.read_permission = True  ✓           │
│  Доступ разрешен                            │
└─────────────────────────────────────────────┘
         ↓
┌─ MockProductViewSet.list() ─────────────────┐
│  # Фильтрация на уровне бизнес-логики:      │
│  if user has read_permission (not read_all):│
│      products = [p for p in MOCK_PRODUCTS   │
│                  if p.owner == request.user.id]
│  else:                                      │
│      products = MOCK_PRODUCTS               │
│                                             │
│  Response: {                                │
│      "results": [                           │
│          {"id": 1, "name": "Мой товар", ...}│
│      ]                                      │
│  }                                          │
└─────────────────────────────────────────────┘
```

**Результат:** **200 OK**, пользователь видит только свои продукты (где `owner == user.id`)

---

##### Сценарий 2: Удаление чужого продукта (роль "user")

```python
# Запрос
DELETE /api/mock/products/5/
Authorization: Bearer eyJhbGc...

# Пользователь: id=1
# Продукт: MockProduct(id=5, owner=2)  ← владелец другой!
# Правила доступа:
AccessRule(
    role=Role(code='user'),
    element=BusinessElement(code='products'),
    delete_permission=True,        # ✓ Может удалять СВОИ
    delete_all_permission=False,   # ✗ Не может удалять ВСЕ
)

# Выполнение:
┌─ IsAuthenticated.has_permission() ──────────┐
│  request.user.is_authenticated? → True  ✓   │
└─────────────────────────────────────────────┘
         ↓
┌─ HasResourcePermission.has_permission() ────┐
│  required_permissions = ('delete_all_permission', 'delete_permission')
│  rule.delete_permission = True  ✓           │
│  Доступ разрешен (на уровне коллекции)      │
└─────────────────────────────────────────────┘
         ↓
┌─ MockProductViewSet.destroy() ──────────────┐
│  product = get_product(pk=5)                │
│  product.owner = 2                          │
└─────────────────────────────────────────────┘
         ↓
┌─ HasResourcePermission.has_object_permission()
│  owner_field = 'owner'                      │
│  is_owner = (product.owner == request.user.id)
│           = (2 == 1) → False  ✗             │
│                                             │
│  Проверка прав:                             │
│  - delete_permission && is_owner?           │
│    True && False → False  ✗                 │
│  - delete_all_permission?                   │
│    False  ✗                                 │
│                                             │
│  → Ни одно условие не выполнено             │
│  → Доступ запрещен                          │
└─────────────────────────────────────────────┘

Response: 403 Forbidden
{
    "detail": "Недостаточно прав для доступа к объекту"
}
```

**Результат:** **403 Forbidden**, нельзя удалить чужой объект

---

##### Сценарий 3: Просмотр чужого продукта (роль "manager")

```python
# Запрос
GET /api/mock/products/5/
Authorization: Bearer eyJhbGc...

# Пользователь: id=1
# Продукт: MockProduct(id=5, owner=2)
# Правила доступа:
AccessRule(
    role=Role(code='manager'),
    element=BusinessElement(code='products'),
    read_permission=False,         # ✗
    read_all_permission=True,      # ✓ Может читать ВСЕ
)

# Выполнение:
┌─ IsAuthenticated.has_permission() ──────────┐
│  True  ✓                                    │
└─────────────────────────────────────────────┘
         ↓
┌─ HasResourcePermission.has_permission() ────┐
│  rule.read_all_permission = True  ✓         │
│  Доступ разрешен                            │
└─────────────────────────────────────────────┘
         ↓
┌─ MockProductViewSet.retrieve() ─────────────┐
│  product = get_product(pk=5)                │
└─────────────────────────────────────────────┘
         ↓
┌─ HasResourcePermission.has_object_permission()
│  is_owner = False  ✗                        │
│  read_all_permission = True  ✓              │
│  → Доступ разрешен                          │
└─────────────────────────────────────────────┘

Response: 200 OK
{
    "id": 5,
    "name": "Наушники",
    "owner_id": 2,
    "is_mine": false
}
```

**Результат:** **200 OK**, менеджер может видеть все продукты

---

##### Сценарий 4: Доступ к административному API (роль "user")

```python
# Запрос
GET /api/users/
Authorization: Bearer eyJhbGc...

# Роли пользователя: ["user"]

# ViewSet:
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminRole]

# Выполнение:
┌─ IsAuthenticated.has_permission() ──────────┐
│  True  ✓                                    │
└─────────────────────────────────────────────┘
         ↓
┌─ IsAdminRole.has_permission() ──────────────┐
│  request.user.user_roles.filter(            │
│      role__code='admin'                     │
│  ).exists()                                 │
│  → False  ✗                                 │
│                                             │
│  → Доступ запрещен                          │
└─────────────────────────────────────────────┘

Response: 403 Forbidden
{
    "detail": "Требуются права администратора"
}
```

**Результат:** **403 Forbidden**, нет роли администратора


#### Примеры проверки прав

**Сценарий 1: Чтение списка товаров**
```python
# Пользователь с ролью "user" запрашивает GET /api/products/
# У роли "user" установлено:
# - read_permission = True
# - read_all_permission = False

# Результат: пользователь увидит только товары где owner_id = его user.id
```

**Сценарий 2: Удаление товара**
```python
# Пользователь с ролью "manager" запрашивает DELETE /api/products/123/
# У роли "manager" установлено:
# - delete_all_permission = True

# Результат: товар будет удален независимо от owner_id
```

**Сценарий 3: Обновление профиля другого пользователя**
```python
# Пользователь с ролью "user" запрашивает PUT /api/users/456/
# У роли "user" установлено:
# - update_permission = True (только свои)
# - update_all_permission = False

# Результат: 403 Forbidden, т.к. owner_id (456) != текущий user.id
```

### API управления

- **Администратор** может управлять ролями, пользователями и правилами доступа через API
- Mock-views для демонстрации работы системы (products, stores, orders)

### Swagger API документация

[`API Endpoints`](http://localhost:8000/api/doc/)

### Документация

[`Sphinx документация`](http://localhost:8000/sphinx/) доступна режиме разработки DEBUG=True
