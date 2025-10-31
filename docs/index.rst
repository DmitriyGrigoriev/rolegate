Система аутентификации и авторизации
====================================

Полнофункциональная система аутентификации и авторизации на Django REST Framework с собственной реализацией JWT токенов и гранулярной системой прав доступа (RBAC).

.. toctree::
   :maxdepth: 2
   :caption: Установка и настройка

   pages/template/CHECKLIST
   pages/template/INSTALLATION_GUIDE

.. toctree::
   :maxdepth: 2
   :caption: Архитектура и дизайн

   pages/template/AUTH_SYSTEM
   pages/template/DATABASE_SCHEMA

.. toctree::
   :maxdepth: 2
   :caption: Справочная информация


Быстрый старт
=============

Для начала работы с системой аутентификации выполните следующие шаги:

**Установка зависимостей**:

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

**Настройте .env**:

  POSTGRES_DB=rolegate
  POSTGRES_USER=rolegate
  POSTGRES_PASSWORD=rolegate

**Применение миграций**:

    python manage.py migrate

**Статические файлы**:

    python manage.py collectstatic --clear

**Инициализация системы**:

    python manage.py init_auth_system

**Запуск сервера**:

    python manage.py runserver 0.0.0.0:8000

Тестовые данные
---------------

После инициализации системы доступен тестовый администратор:

* Email: ``admin@example.com``
* Пароль: ``Admin123!``

Основные возможности
====================

✅ **Аутентификация**
   - Регистрация пользователей с валидацией
   - Вход/выход из системы
   - JWT токены (access и refresh)
   - Управление сессиями
   - Мягкое удаление аккаунтов

✅ **Авторизация**
   - Ролевая модель доступа (RBAC)
   - Гранулярные права (7 типов разрешений)
   - Разделение прав "свои/все объекты"
   - Проверка владельца объекта
   - API для управления правами

✅ **Управление**
   - Административный интерфейс Django
   - API для управления пользователями
   - API для управления ролями и правами
   - Назначение/отзыв ролей

✅ **Демонстрация**
   - Mock ViewSets для продуктов, магазинов, заказов
   - Работающие примеры проверки прав
   - Тестовые данные из коробки

Технологии
==========

* **Django 5+** - веб-фреймворк
* **Django REST Framework** - RESTful API
* **PostgreSQL** - база данных
* **PyJWT** - JWT токены
* **bcrypt** - хеширование паролей

Структура документации
=======================

:doc:`pages/template/CHECKLIST`
   Пошаговый чеклист установки и проверки системы

:doc:`pages/template/INSTALLATION_GUIDE`
   Подробная инструкция по установке и настройке

:doc:`pages/template/AUTH_SYSTEM`
   Полное описание архитектуры системы аутентификации и авторизации

:doc:`pages/template/DATABASE_SCHEMA`
   Детальная схема базы данных с ER-диаграммами

API Endpoints
=============

Аутентификация
--------------

.. code-block:: none

   POST   /api/auth/register/     - Регистрация нового пользователя
   POST   /api/auth/login/        - Вход в систему
   POST   /api/auth/logout/       - Выход из системы
   POST   /api/auth/refresh/      - Обновление access токена
   GET    /api/auth/me/           - Получение информации о текущем пользователе
   PUT    /api/auth/me/           - Обновление профиля
   DELETE /api/auth/me/           - Удаление аккаунта

Управление пользователями (только для администраторов)
-------------------------------------------------------

.. code-block:: none

   GET    /api/users/             - Список всех пользователей
   GET    /api/users/{id}/        - Информация о пользователе
   POST   /api/users/             - Создание пользователя
   PUT    /api/users/{id}/        - Обновление пользователя
   DELETE /api/users/{id}/        - Удаление пользователя
   POST   /api/users/{id}/assign-role/  - Назначить роль
   DELETE /api/users/{id}/roles/{role_id}/  - Отозвать роль

Управление системой (только для администраторов)
-------------------------------------------------

.. code-block:: none

   GET    /api/roles/             - Список ролей
   POST   /api/roles/             - Создание роли
   GET    /api/access-rules/      - Список правил доступа
   POST   /api/access-rules/      - Создание правила доступа

Mock API (демонстрация работы прав)
------------------------------------

.. code-block:: none

   GET    /api/mock/products/     - Список продуктов
   POST   /api/mock/products/     - Создание продукта
   GET    /api/mock/products/{id}/  - Детали продукта
   PUT    /api/mock/products/{id}/  - Обновление продукта
   DELETE /api/mock/products/{id}/  - Удаление продукта

Аналогично для ``/api/mock/stores/`` и ``/api/mock/orders/``

Пример использования
====================

Регистрация и вход
------------------

.. code-block:: python

   import requests

   BASE_URL = 'http://localhost:8000/api'

   # Регистрация
   response = requests.post(f'{BASE_URL}/auth/register/', json={
       'email': 'user@example.com',
       'password': 'SecurePass123!',
       'password_confirm': 'SecurePass123!',
       'first_name': 'Иван',
       'last_name': 'Иванов'
   })

   # Вход
   response = requests.post(f'{BASE_URL}/auth/login/', json={
       'email': 'user@example.com',
       'password': 'SecurePass123!'
   })

   tokens = response.json()['tokens']
   access_token = tokens['access_token']

Запрос с токеном
----------------

.. code-block:: python

   # Запрос с авторизацией
   headers = {'Authorization': f'Bearer {access_token}'}
   response = requests.get(f'{BASE_URL}/mock/products/', headers=headers)

   products = response.json()
   print(f"Найдено продуктов: {products['count']}")

Структура ролей
===============

Предустановленные роли
----------------------

**admin** - Администратор
   Полный доступ ко всем ресурсам и функциям системы

**manager** - Менеджер
   Управление бизнес-объектами (продукты, магазины, заказы)

**user** - Пользователь
   Работа со своими объектами, ограниченный доступ к чужим

**guest** - Гость
   Только чтение публичных данных

Типы разрешений
---------------

* ``read_permission`` - Чтение своих объектов
* ``read_all_permission`` - Чтение всех объектов
* ``create_permission`` - Создание объектов
* ``update_permission`` - Обновление своих объектов
* ``update_all_permission`` - Обновление всех объектов
* ``delete_permission`` - Удаление своих объектов
* ``delete_all_permission`` - Удаление всех объектов

Безопасность
============

- **Хеширование паролей**
   Использование bcrypt

- **JWT токены**
   * Access token: 15 минут
   * Refresh token: 7 дней
   * Токены хранятся хешированными

- **Отслеживание сессий**
   Сохранение IP адреса и User-Agent

- **Мягкое удаление**
   Пользователи помечаются как неактивные вместо удаления

- **Проверка прав**
   Автоматическая проверка на уровне ViewSet

Тестирование
============

Запуск тестов::

   python manage.py test server.apps.authentication

Тесты покрывают:

* Регистрацию пользователей
* Аутентификацию JWT
* Проверку прав доступа
* Управление ролями
* CRUD операции

Индексы и таблицы
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
