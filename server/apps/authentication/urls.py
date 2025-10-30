"""
URL конфигурация для приложения authentication.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AuthViewSet,
    UserViewSet,
    RoleViewSet,
    BusinessElementViewSet,
    AccessRuleViewSet,
)
from .mock_views import MockProductViewSet, MockStoreViewSet, MockOrderViewSet

# Создаем router для ViewSets
router = DefaultRouter()

# Регистрируем ViewSets
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'business-elements', BusinessElementViewSet, basename='business-element')
router.register(r'access-rules', AccessRuleViewSet, basename='access-rule')

# Mock ViewSets
router.register(r'mock/products', MockProductViewSet, basename='mock-product')
router.register(r'mock/stores', MockStoreViewSet, basename='mock-store')
router.register(r'mock/orders', MockOrderViewSet, basename='mock-order')

# URL patterns для auth endpoints
auth_patterns = [
    path('register/', AuthViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),
    path('refresh/', AuthViewSet.as_view({'post': 'refresh'}), name='auth-refresh'),
    path('me/', AuthViewSet.as_view({
        'get': 'me',
        'put': 'update_profile',
        'patch': 'update_profile',
        'delete': 'delete_account',
    }), name='auth-me'),
]

app_name = 'authentication'

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('', include(router.urls)),
    # path('', include(mock_patterns)),
]
