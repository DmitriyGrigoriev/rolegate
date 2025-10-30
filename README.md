# Доступ на основе ролей - rolegate


Этот проект был создан с помощью [`wemake-django-template`](https://github.com/wemake-services/wemake-django-template). Текущая версия шаблона: [3b6ab46](https://github.com/wemake-services/wemake-django-template/tree/3b6ab4692b7436ed9255ed7521bd204b41f118f5). Последнии обновления [updated](https://github.com/wemake-services/wemake-django-template/compare/3b6ab4692b7436ed9255ed7521bd204b41f118f5...master)


[![wemake.services](https://img.shields.io/badge/%20-wemake.services-green.svg?label=%20&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC%2FxhBQAAAAFzUkdCAK7OHOkAAAAbUExURQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP%2F%2F%2F5TvxDIAAAAIdFJOUwAjRA8xXANAL%2Bv0SAAAADNJREFUGNNjYCAIOJjRBdBFWMkVQeGzcHAwksJnAPPZGOGAASzPzAEHEGVsLExQwE7YswCb7AFZSF3bbAAAAABJRU5ErkJggg%3D%3D)](https://wemake-services.github.io)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)


## Предварительные требования

Вам понадобятся:

- `python3.11` (see `pyproject.toml` for exact version), use `pyenv install`
- `postgresql` (see `docker-compose.yml` for exact version)
- Latest `docker`


## Разработка

При локальной разработке используется:
- [`poetry`](https://github.com/python-poetry/poetry) (**required**)
- [`pyenv`](https://github.com/pyenv/pyenv)



### Архитектура

Проект реализует собственную систему аутентификации и авторизации на основе ролей (RBAC) с гранулярным управлением правами доступа.

### Схема базы данных

#### Основные таблицы

**users** — Пользователи системы
- `id`, `email` (уникальный), `password` (bcrypt), `first_name`, `last_name`, `middle_name`
- `is_active` — для мягкого удаления
- `created_at`, `updated_at`

**roles** — Роли в системе
- `id`, `name`, `code` (уникальный: admin, manager, user, guest)
- `description`

**user_roles** — Связь пользователей и ролей
- `user_id`, `role_id`, `assigned_at`

**business_elements** — Объекты приложения, к которым настраивается доступ
- `id`, `name`, `code` (уникальный: users, products, stores, orders, access_rules)
- `description`

**access_rules** — Правила доступа роли к бизнес-элементу
- `role_id`, `element_id`
- Флаги разрешений:
  - `read_permission` — чтение своих объектов (созданных пользователем)
  - `read_all_permission` — чтение всех объектов
  - `create_permission` — создание объектов
  - `update_permission` — обновление своих объектов
  - `update_all_permission` — обновление всех объектов
  - `delete_permission` — удаление своих объектов
  - `delete_all_permission` — удаление всех объектов

**sessions** — Сессии пользователей (JWT-токены)
- `user_id`, `token`, `expires_at`, `is_active`

### Принципы работы

1. **Аутентификация**: JWT-токены + сессии в БД
2. **Авторизация**: Проверка прав через middleware на основе роли пользователя и правил доступа
3. **Разграничение**: "Свои объекты" vs "Все объекты" (через поле `owner_id` в бизнес-объектах)
4. **Коды ответов**: 401 (не аутентифицирован), 403 (нет прав доступа)

### API управления

- **Администратор** может управлять ролями, пользователями и правилами доступа через API
- Mock-views для демонстрации работы системы (products, stores, orders)

### Swagger API документация

[`API Endpoints`](http://localhost:8000/api/doc/)

### Документация

[`Sphinx документация`](http://localhost:8000/sphinx/) доступна режиме разработки DEBUG=True
