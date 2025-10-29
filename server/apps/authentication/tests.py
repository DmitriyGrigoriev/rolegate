"""
Тесты для системы аутентификации и авторизации.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import User, Role, UserRole, BusinessElement, AccessRule
from .utils import generate_access_token, decode_token


class UserModelTest(TestCase):
    """Тесты для модели User."""

    def test_create_user(self):
        """Тест создания пользователя."""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Тест создания суперпользователя."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
        )

        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_get_full_name(self):
        """Тест получения полного имени."""
        user = User.objects.create_user(
            email='test@example.com',
            password='test',
            first_name='Иван',
            last_name='Иванов',
            middle_name='Иванович',
        )

        self.assertEqual(user.get_full_name(), 'Иванов Иван Иванович')


class JWTUtilsTest(TestCase):
    """Тесты для утилит JWT."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test',
        )

    def test_generate_and_decode_token(self):
        """Тест генерации и декодирования токена."""
        token, expires_at = generate_access_token(self.user.id)

        self.assertIsNotNone(token)
        self.assertIsNotNone(expires_at)

        payload = decode_token(token)
        self.assertEqual(payload['user_id'], self.user.id)
        self.assertEqual(payload['type'], 'access')


class AuthenticationAPITest(APITestCase):
    """Тесты для API аутентификации."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()

        # Создаем роль "user"
        self.user_role = Role.objects.create(
            name='Пользователь',
            code='user',
        )

    def test_register(self):
        """Тест регистрации."""
        url = reverse('authentication:auth-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

        # Проверяем, что пользователь создан в БД
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(user.is_active)

    def test_register_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями."""
        url = reverse('authentication:auth-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'Pass123!',
            'password_confirm': 'Different123!',
            'first_name': 'New',
            'last_name': 'User',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        """Тест входа."""
        # Создаем пользователя
        User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
        )

        url = reverse('authentication:auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access_token', response.data['tokens'])
        self.assertIn('refresh_token', response.data['tokens'])

    def test_login_wrong_password(self):
        """Тест входа с неверным паролем."""
        User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
        )

        url = reverse('authentication:auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Тест входа с неактивным пользователем."""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
        )
        user.is_active = False
        user.save()

        url = reverse('authentication:auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_current_user(self):
        """Тест получения информации о текущем пользователе."""
        # Создаем пользователя
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
        )

        # Генерируем токен
        token, _ = generate_access_token(user.id)

        # Делаем запрос с токеном
        url = reverse('authentication:auth-me')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')


class PermissionsTest(APITestCase):
    """Тесты для проверки прав доступа."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()

        # Создаем роли
        self.admin_role = Role.objects.create(name='Администратор', code='admin')
        self.user_role = Role.objects.create(name='Пользователь', code='user')

        # Создаем бизнес-элементы
        self.products_element = BusinessElement.objects.create(
            name='Продукты',
            code='products',
        )

        # Создаем правила доступа
        AccessRule.objects.create(
            role=self.admin_role,
            element=self.products_element,
            read_all_permission=True,
            create_permission=True,
            update_all_permission=True,
            delete_all_permission=True,
        )

        AccessRule.objects.create(
            role=self.user_role,
            element=self.products_element,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )

        # Создаем пользователей
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='admin',
        )
        UserRole.objects.create(user=self.admin, role=self.admin_role)

        self.user = User.objects.create_user(
            email='user@example.com',
            password='user',
        )
        UserRole.objects.create(user=self.user, role=self.user_role)

    def test_admin_can_access_products(self):
        """Тест: администратор может получить доступ к продуктам."""
        token, _ = generate_access_token(self.admin.id)

        url = reverse('authentication:mock-product-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_access_products(self):
        """Тест: обычный пользователь может получить доступ к продуктам."""
        token, _ = generate_access_token(self.user.id)

        url = reverse('authentication:mock-product-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_access(self):
        """Тест: неаутентифицированный пользователь не может получить доступ."""
        url = reverse('authentication:mock-product-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
