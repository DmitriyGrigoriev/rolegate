# Чеклист установки системы аутентификации и авторизации

## Шаги для запуска

### Установка зависимостей

```bash
# Установка Poetry (если еще не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка Poetry Shell
poetry self add poetry-plugin-shell

# Установка зависимостей проекта
poetry install

# Активация виртуального окружения
poetry shell

# Подготовка документации
cd docs
make clean && make html


```
### Настройка Django

#### JWT настройки
`server/settings/components/auth.py`
```python
JWT_SECRET_KEY = 'your-secret-key-here'  # Смените на свой!
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = 15  # минуты
JWT_REFRESH_TOKEN_LIFETIME = 7  # дни
```

### Применение миграций:

```bash
# Применение миграций
python manage.py migrate
```

### Инициализация системы

```bash
python manage.py init_auth_system
```

### Статические файлы

```bash
python manage.py collectstatic -y
```

Эта команда создаст:
- ✅ 4 роли (admin, manager, user, guest)
- ✅ 5 бизнес-элементов (users, products, stores, orders, access_rules)
- ✅ Правила доступа для всех ролей
- ✅ Тестового администратора:
  - Email: `admin@example.com`
  - Пароль: `Admin123!`

### Запуск сервера

```bash
python manage.py runserver
```

### Тестирование

#### Через Postman:
1. Импортируйте файл `postman_collection.json` коллекция для Postman
2. Выполните запрос "Login" из папки "Authentication"
3. Получите токены `access_token` и `refresh_token` и сохраните в переменные
4. Тестируйте другие endpoints

#### Через Swagger API:
`http://localhost:8000/api/doc/`

#### Через curl:
```bash
# Вход администратора
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!"}'
```

#### Через Python:
```python
import requests

response = requests.post('http://localhost:8000/api/auth/login/', json={
    "email": "admin@example.com",
    "password": "Admin123!"
})
token = response.json()['tokens']['access_token']

# Запрос с токеном
headers = {'Authorization': f'Bearer {token}'}
products = requests.get('http://localhost:8000/api/mock/products/', headers=headers)
print(products.json())
```

## Запуск тестов

```bash
python manage.py test server.apps.authentication
```

## Проверка работы

### API Endpoints для проверки:

1. **Регистрация** (без токена):
   ```
   POST /api/auth/register/
   ```

2. **Вход** (без токена):
   ```
   POST /api/auth/login/
   ```

3. **Текущий пользователь** (с токеном):
   ```
   GET /api/auth/me/
   ```

4. **Mock продукты** (с токеном):
   ```
   GET /api/mock/products/
   ```

5. **Управление пользователями** (только админ):
   ```
   GET /api/users/
   ```

6. **Управление правами** (только админ):
   ```
   GET /api/access-rules/
   ```

## Основные возможности

### Реализовано:

✅ **Аутентификация**
- Регистрация с валидацией паролей
- Вход по email/password
- JWT токены (access + refresh)
- Управление сессиями
- Автоматический logout при деактивации
- Мягкое удаление аккаунтов

✅ **Авторизация**
- Ролевая модель (RBAC)
- Гранулярные права (7 типов)
- Разделение "свои/все объекты"
- Проверка владельца
- Multiple roles per user

✅ **API**
- RESTful API для всех операций
- DRF serializers с валидацией
- Пагинация
- Фильтрация
- Документированные endpoints

✅ **Безопасность**
- bcrypt для паролей
- JWT с коротким временем жизни
- Хеширование токенов в БД
- Отслеживание IP и User-Agent
- Валидация токенов при каждом запросе

✅ **Управление**
- Django Admin интерфейс
- API для администраторов
- Management команды
- Тестовые данные

✅ **Демонстрация**
- Mock ViewSets
- Postman коллекция
- Примеры использования
- Unit тесты

### Ошибка: 401 Unauthorized
- Проверьте, что токен передается в заголовке
- Формат: `Authorization: Bearer YOUR_TOKEN`
- Проверьте срок действия токена (15 минут)

### Ошибка: 403 Forbidden
- Проверьте права пользователя в БД
- Убедитесь, что правила доступа созданы
- Проверьте `resource_code` в ViewSet

Система полностью готова к использованию.

1. ✅ Собственная аутентификация (не из коробки)
2. ✅ JWT токены (bcrypt + PyJWT)
3. ✅ Кастомный middleware
4. ✅ Ролевая система с гранулярными правами
5. ✅ Разграничение доступа к ресурсам
6. ✅ API для управления правами
7. ✅ Mock Views для демонстрации
8. ✅ Тестовые данные
9. ✅ Документация


### Основное приложение
- [x] `server/apps/authentication/__init__.py` - инициализация пакета
- [x] `server/apps/authentication/apps.py` - конфигурация приложения
- [x] `server/apps/authentication/models.py` - модели БД
- [x] `server/apps/authentication/serializers.py` - сериализаторы DRF
- [x] `server/apps/authentication/views.py` - API views
- [x] `server/apps/authentication/mock_views.py` - демонстрационные views
- [x] `server/apps/authentication/permissions.py` - проверка прав
- [x] `server/apps/authentication/middleware.py` - JWT middleware
- [x] `server/apps/authentication/utils.py` - утилиты JWT
- [x] `server/apps/authentication/urls.py` - URL маршруты
- [x] `server/apps/authentication/tests.py` - тесты

### Management команды
- [x] `server/apps/authentication/management/commands/init_auth_system.py` - инициализация системы

### Документация
- [x] `docs/pages/template/CHECKLIST.md` - установка системы
- [x] `docs/pages/template/AUTH_SYSTEM.md` - полное описание архитектуры
- [x] `docs/pages/template/DATABASE_SCHEMA.md` - ER-диаграмма
- [x] `README.md` - краткое описание
- [x] `pyproject.toml` - зависимости
- [x] `postman_collection.json` - коллекция для Postman
