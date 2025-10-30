# Схема базы данных системы аутентификации

## ER-диаграмма (текстовое представление)

```
┌─────────────────────────────────┐
│          users                  │
├─────────────────────────────────┤
│ PK │ id                         │
│    │ email (unique)             │
│    │ password (hashed)          │
│    │ first_name                 │
│    │ last_name                  │
│    │ middle_name                │
│    │ is_active                  │
│    │ is_staff                   │
│    │ is_superuser               │
│    │ created_at                 │
│    │ updated_at                 │
└─────────────────────────────────┘
           │
           │ 1:N
           ↓
┌─────────────────────────────────┐
│        user_roles               │
├─────────────────────────────────┤
│ PK │ id                         │
│ FK │ user_id                    │
│ FK │ role_id                    │
│ FK │ assigned_by (nullable)     │
│    │ assigned_at                │
└─────────────────────────────────┘
           │
           │ N:1
           ↓
┌─────────────────────────────────┐
│          roles                  │
├─────────────────────────────────┤
│ PK │ id                         │
│    │ name (unique)              │
│    │ code (unique)              │
│    │ description                │
│    │ created_at                 │
└─────────────────────────────────┘
           │
           │ 1:N
           ↓
┌─────────────────────────────────┐
│       access_rules              │
├─────────────────────────────────┤
│ PK │ id                         │
│ FK │ role_id                    │
│ FK │ element_id                 │
│    │ read_permission            │
│    │ read_all_permission        │
│    │ create_permission          │
│    │ update_permission          │
│    │ update_all_permission      │
│    │ delete_permission          │
│    │ delete_all_permission      │
│    │ created_at                 │
│    │ updated_at                 │
│    │ UNIQUE(role_id, element_id)│
└─────────────────────────────────┘
           │
           │ N:1
           ↓
┌─────────────────────────────────┐
│     business_elements           │
├─────────────────────────────────┤
│ PK │ id                         │
│    │ name (unique)              │
│    │ code (unique)              │
│    │ description                │
│    │ created_at                 │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│         sessions                │
├─────────────────────────────────┤
│ PK │ id                         │
│ FK │ user_id                    │
│    │ token_hash (indexed)       │
│    │ refresh_token_hash         │
│    │ expires_at (indexed)       │
│    │ refresh_expires_at         │
│    │ ip_address                 │
│    │ user_agent                 │
│    │ is_active (indexed)        │
│    │ created_at                 │
└─────────────────────────────────┘
           │
           │ N:1
           ↓
        users
```

## Связи таблиц

### 1. users ←→ user_roles (1:N)
- Один пользователь может иметь несколько ролей
- Связь: `user_roles.user_id → users.id`

### 2. roles ←→ user_roles (1:N)
- Одна роль может быть у многих пользователей
- Связь: `user_roles.role_id → roles.id`

### 3. roles ←→ access_rules (1:N)
- Одна роль может иметь множество правил доступа
- Связь: `access_rules.role_id → roles.id`

### 4. business_elements ←→ access_rules (1:N)
- Один бизнес-элемент может иметь правила для разных ролей
- Связь: `access_rules.element_id → business_elements.id`

### 5. users ←→ sessions (1:N)
- Один пользователь может иметь несколько активных сессий
- Связь: `sessions.user_id → users.id`

### 6. users ←→ user_roles.assigned_by (1:N)
- Один пользователь может назначить роли многим другим
- Связь: `user_roles.assigned_by → users.id` (nullable)

## Индексы

### Таблица users
- PRIMARY KEY (id)
- UNIQUE INDEX (email)
- INDEX (is_active)
- INDEX (created_at)

### Таблица roles
- PRIMARY KEY (id)
- UNIQUE INDEX (name)
- UNIQUE INDEX (code)

### Таблица user_roles
- PRIMARY KEY (id)
- UNIQUE INDEX (user_id, role_id)
- INDEX (user_id)
- INDEX (role_id)
- INDEX (assigned_by)

### Таблица business_elements
- PRIMARY KEY (id)
- UNIQUE INDEX (name)
- UNIQUE INDEX (code)

### Таблица access_rules
- PRIMARY KEY (id)
- UNIQUE INDEX (role_id, element_id)
- INDEX (role_id)
- INDEX (element_id)

### Таблица sessions
- PRIMARY KEY (id)
- INDEX (user_id, is_active)
- INDEX (token_hash, is_active)
- INDEX (expires_at)

## Предустановленные данные

### Роли (roles)
```
id │ code      │ name           │ description
───┼───────────┼────────────────┼─────────────────────────
1  │ admin     │ Администратор  │ Полный доступ
2  │ manager   │ Менеджер       │ Управление бизнес-объектами
3  │ user      │ Пользователь   │ Базовый доступ
4  │ guest     │ Гость          │ Только чтение
```

### Бизнес-элементы (business_elements)
```
id │ code         │ name            │ description
───┼──────────────┼─────────────────┼──────────────────
1  │ users        │ Пользователи    │ Управление пользователями
2  │ products     │ Продукты        │ Управление продуктами
3  │ stores       │ Магазины        │ Управление магазинами
4  │ orders       │ Заказы          │ Управление заказами
5  │ access_rules │ Правила доступа │ Управление авторизацией
```

### Правила доступа (access_rules) - примеры

#### Admin → users
```
read_all ✓ | create ✓ | update_all ✓ | delete_all ✓
```

#### Admin → products, stores, orders, access_rules
```
read_all ✓ | create ✓ | update_all ✓ | delete_all ✓
```

#### Manager → products
```
read_all ✓ | create ✓ | update_all ✓ | delete ✓
```

#### User → products
```
read_all ✓ | create ✓ | update ✓ | delete ✓
```

#### Guest → products
```
read_all ✓
```

## Типы данных

### users
```sql
id              BIGINT PRIMARY KEY AUTO_INCREMENT
email           VARCHAR(255) UNIQUE NOT NULL
password        VARCHAR(255) NOT NULL
first_name      VARCHAR(150)
last_name       VARCHAR(150)
middle_name     VARCHAR(150)
is_active       BOOLEAN DEFAULT TRUE
is_staff        BOOLEAN DEFAULT FALSE
is_superuser    BOOLEAN DEFAULT FALSE
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW() ON UPDATE NOW()
```

### roles
```sql
id              BIGINT PRIMARY KEY AUTO_INCREMENT
name            VARCHAR(100) UNIQUE NOT NULL
code            VARCHAR(50) UNIQUE NOT NULL
description     TEXT
created_at      TIMESTAMP DEFAULT NOW()
```

### user_roles
```sql
id              BIGINT PRIMARY KEY AUTO_INCREMENT
user_id         BIGINT NOT NULL REFERENCES users(id)
role_id         BIGINT NOT NULL REFERENCES roles(id)
assigned_by     BIGINT NULL REFERENCES users(id)
assigned_at     TIMESTAMP DEFAULT NOW()
UNIQUE(user_id, role_id)
```

### business_elements
```sql
id              BIGINT PRIMARY KEY AUTO_INCREMENT
name            VARCHAR(100) UNIQUE NOT NULL
code            VARCHAR(50) UNIQUE NOT NULL
description     TEXT
created_at      TIMESTAMP DEFAULT NOW()
```

### access_rules
```sql
id                      BIGINT PRIMARY KEY AUTO_INCREMENT
role_id                 BIGINT NOT NULL REFERENCES roles(id)
element_id              BIGINT NOT NULL REFERENCES business_elements(id)
read_permission         BOOLEAN DEFAULT FALSE
read_all_permission     BOOLEAN DEFAULT FALSE
create_permission       BOOLEAN DEFAULT FALSE
update_permission       BOOLEAN DEFAULT FALSE
update_all_permission   BOOLEAN DEFAULT FALSE
delete_permission       BOOLEAN DEFAULT FALSE
delete_all_permission   BOOLEAN DEFAULT FALSE
created_at              TIMESTAMP DEFAULT NOW()
updated_at              TIMESTAMP DEFAULT NOW() ON UPDATE NOW()
UNIQUE(role_id, element_id)
```

### sessions
```sql
id                  BIGINT PRIMARY KEY AUTO_INCREMENT
user_id             BIGINT NOT NULL REFERENCES users(id)
token_hash          VARCHAR(255) NOT NULL
refresh_token_hash  VARCHAR(255) NOT NULL
expires_at          TIMESTAMP NOT NULL
refresh_expires_at  TIMESTAMP NOT NULL
ip_address          VARCHAR(45)
user_agent          TEXT
is_active           BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP DEFAULT NOW()
```

## Запросы для проверки

### Получить все роли пользователя
```sql
SELECT r.name, r.code
FROM roles r
JOIN user_roles ur ON r.id = ur.role_id
WHERE ur.user_id = 1;
```

### Получить права роли для элемента
```sql
SELECT ar.*
FROM access_rules ar
JOIN roles r ON ar.role_id = r.id
JOIN business_elements be ON ar.element_id = be.id
WHERE r.code = 'user' AND be.code = 'products';
```

### Получить все права пользователя
```sql
SELECT 
    r.name as role_name,
    be.name as element_name,
    ar.read_permission,
    ar.read_all_permission,
    ar.create_permission,
    ar.update_permission,
    ar.update_all_permission,
    ar.delete_permission,
    ar.delete_all_permission
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN access_rules ar ON r.id = ar.role_id
JOIN business_elements be ON ar.element_id = be.id
WHERE u.email = 'user@example.com';
```

### Активные сессии пользователя
```sql
SELECT *
FROM sessions
WHERE user_id = 1 
  AND is_active = TRUE
  AND expires_at > NOW();
```

## Размер данных (примерная оценка)

### На 10,000 пользователей:
```
users:              10,000 rows  (~2 MB)
user_roles:         15,000 rows  (~1 MB, если ~1.5 роли на юзера)
sessions:           50,000 rows  (~10 MB, если 5 сессий на юзера)
roles:              4 rows       (~1 KB)
business_elements:  5 rows       (~1 KB)
access_rules:       20 rows      (~2 KB)
──────────────────────────────────────────
TOTAL:              ~13 MB
```

## Нормализация

База данных находится в **третьей нормальной форме (3NF)**:

1. ✅ Все атрибуты атомарны
2. ✅ Все неключевые атрибуты зависят от первичного ключа
3. ✅ Нет транзитивных зависимостей
4. ✅ Минимум дублирования данных
5. ✅ Связи через внешние ключи

## Производительность

### Оптимизации:
- Индексы на часто используемых полях
- UNIQUE индексы для предотвращения дубликатов
- Составные индексы для JOIN операций
- Кеширование токенов в памяти (можно добавить Redis)
- Lazy loading для связанных объектов

### Узкие места:
- JOIN при проверке прав (можно кешировать)
- Поиск активных сессий (индекс решает)
- Множественные роли у пользователя (приемлемо)
