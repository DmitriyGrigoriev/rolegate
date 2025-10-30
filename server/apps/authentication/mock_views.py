"""
Mock Views для демонстрации работы системы авторизации.

Эти views не используют реальные модели БД, а возвращают тестовые данные,
демонстрируя работу проверки прав доступа.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .permissions import IsAuthenticated, HasResourcePermission
from .serializers import MockProductSerializer, MockStoreSerializer, MockOrderSerializer


class MockProduct:
    """Mock класс для продукта."""

    def __init__(self, id, name, price, owner_id):
        self.id = id
        self.name = name
        self.price = price
        self.owner = owner_id  # ID владельца


# Тестовые данные продуктов
MOCK_PRODUCTS = [
    MockProduct(1, 'Ноутбук', 50000, 1),
    MockProduct(2, 'Мышка', 500, 1),
    MockProduct(3, 'Клавиатура', 1500, 2),
    MockProduct(4, 'Монитор', 15000, 2),
    MockProduct(5, 'Наушники', 3000, 3),
]


class MockProductViewSet(viewsets.ViewSet):
    """
    Mock ViewSet для продуктов.

    Демонстрирует работу системы авторизации без реальной БД.
    """

    serializer_class = MockProductSerializer
    permission_classes = [IsAuthenticated, HasResourcePermission]
    resource_code = 'products'
    owner_field = 'owner'

    def list(self, request):
        """
        Получение списка продуктов.

        GET /api/mock/products/
        """
        # В реальном приложении здесь была бы фильтрация на основе прав
        products_data = [
            {
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'owner_id': p.owner,
                'is_mine': p.owner == request.user.id,
            }
            for p in MOCK_PRODUCTS
        ]

        return Response({
            'count': len(products_data),
            'results': products_data,
        })

    def retrieve(self, request, pk=None):
        """
        Получение детальной информации о продукте.

        GET /api/mock/products/{id}/
        """
        product = next((p for p in MOCK_PRODUCTS if p.id == int(pk)), None)

        if not product:
            return Response(
                {'error': 'Продукт не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверяем права на объект
        if not self.check_object_permission(request, product):
            return Response(
                {'error': 'Недостаточно прав для доступа к этому продукту'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'owner_id': product.owner,
            'is_mine': product.owner == request.user.id,
        })

    def create(self, request):
        """
        Создание нового продукта.

        POST /api/mock/products/
        """
        name = request.data.get('name')
        price = request.data.get('price')

        if not name or not price:
            return Response(
                {'error': 'name и price обязательны'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # В реальном приложении здесь было бы создание в БД
        new_id = max(p.id for p in MOCK_PRODUCTS) + 1
        new_product = {
            'id': new_id,
            'name': name,
            'price': price,
            'owner_id': request.user.id,
            'is_mine': True,
        }

        return Response(
            {
                'message': 'Продукт успешно создан',
                'product': new_product,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, pk=None):
        """
        Обновление продукта.

        PUT /api/mock/products/{id}/
        """
        product = next((p for p in MOCK_PRODUCTS if p.id == int(pk)), None)

        if not product:
            return Response(
                {'error': 'Продукт не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверяем права на объект
        if not self.check_object_permission(request, product):
            return Response(
                {'error': 'Недостаточно прав для обновления этого продукта'},
                status=status.HTTP_403_FORBIDDEN,
            )

        name = request.data.get('name', product.name)
        price = request.data.get('price', product.price)

        return Response({
            'message': 'Продукт успешно обновлен',
            'product': {
                'id': product.id,
                'name': name,
                'price': price,
                'owner_id': product.owner,
                'is_mine': product.owner == request.user.id,
            },
        })

    def partial_update(self, request, pk=None):
        """
        Частичное обновление продукта.

        PATCH /api/mock/products/{id}/
        """
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        """
        Удаление продукта.

        DELETE /api/mock/products/{id}/
        """
        product = next((p for p in MOCK_PRODUCTS if p.id == int(pk)), None)

        if not product:
            return Response(
                {'error': 'Продукт не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверяем права на объект
        if not self.check_object_permission(request, product):
            return Response(
                {'error': 'Недостаточно прав для удаления этого продукта'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({
            'message': 'Продукт успешно удален',
        })

    def check_object_permission(self, request, obj):
        """Проверка прав на уровне объекта."""
        for permission in self.permission_classes:
            perm = permission()
            if hasattr(perm, 'has_object_permission'):
                if not perm.has_object_permission(request, self, obj):
                    return False
        return True


# Mock данные для магазинов
MOCK_STORES = [
    {'id': 1, 'name': 'Магазин на Невском', 'address': 'Невский пр., 1', 'owner': 1},
    {'id': 2, 'name': 'Магазин в центре', 'address': 'Центральная ул., 5', 'owner': 2},
    {'id': 3, 'name': 'Магазин у метро', 'address': 'Метро ул., 10', 'owner': 1},
]


class MockStoreViewSet(viewsets.ViewSet):
    """Mock ViewSet для магазинов."""

    serializer_class = MockStoreSerializer
    permission_classes = [IsAuthenticated, HasResourcePermission]
    resource_code = 'stores'
    owner_field = 'owner'

    def list(self, request):
        """Список магазинов."""
        stores_data = [
            {**store, 'is_mine': store['owner'] == request.user.id}
            for store in MOCK_STORES
        ]
        return Response({'count': len(stores_data), 'results': stores_data})

    def retrieve(self, request, pk=None):
        """Детальная информация о магазине."""
        store = next((s for s in MOCK_STORES if s['id'] == int(pk)), None)
        if not store:
            return Response(
                {'error': 'Магазин не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({**store, 'is_mine': store['owner'] == request.user.id})

    def create(self, request):
        """Создание магазина."""
        name = request.data.get('name')
        address = request.data.get('address')
        if not name or not address:
            return Response(
                {'error': 'name и address обязательны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_store = {
            'id': max(s['id'] for s in MOCK_STORES) + 1,
            'name': name,
            'address': address,
            'owner': request.user.id,
            'is_mine': True,
        }
        return Response(
            {'message': 'Магазин создан', 'store': new_store},
            status=status.HTTP_201_CREATED,
        )


# Mock данные для заказов
MOCK_ORDERS = [
    {'id': 1, 'product': 'Ноутбук', 'quantity': 1, 'total': 50000, 'owner': 1},
    {'id': 2, 'product': 'Мышка', 'quantity': 2, 'total': 1000, 'owner': 2},
    {'id': 3, 'product': 'Клавиатура', 'quantity': 1, 'total': 1500, 'owner': 1},
]


class MockOrderViewSet(viewsets.ViewSet):
    """Mock ViewSet для заказов."""

    serializer_class = MockOrderSerializer
    permission_classes = [IsAuthenticated, HasResourcePermission]
    resource_code = 'orders'
    owner_field = 'owner'

    @extend_schema(
        operation_id='mock_orders_list',
        description='Get list of all orders'
    )
    def list(self, request):
        """Список заказов."""
        orders_data = [
            {**order, 'is_mine': order['owner'] == request.user.id}
            for order in MOCK_ORDERS
        ]
        return Response({'count': len(orders_data), 'results': orders_data})

    @extend_schema(
        operation_id='mock_orders_detail',
        description='Get specific order by ID'
    )
    def retrieve(self, request, pk=None):
        """Детальная информация о заказе."""
        order = next((o for o in MOCK_ORDERS if o['id'] == int(pk)), None)
        if not order:
            return Response(
                {'error': 'Заказ не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({**order, 'is_mine': order['owner'] == request.user.id})

    def create(self, request):
        """Создание заказа."""
        product = request.data.get('product')
        quantity = request.data.get('quantity')
        total = request.data.get('total')
        if not all([product, quantity, total]):
            return Response(
                {'error': 'product, quantity и total обязательны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_order = {
            'id': max(o['id'] for o in MOCK_ORDERS) + 1,
            'product': product,
            'quantity': quantity,
            'total': total,
            'owner': request.user.id,
            'is_mine': True,
        }
        return Response(
            {'message': 'Заказ создан', 'order': new_order},
            status=status.HTTP_201_CREATED,
        )
