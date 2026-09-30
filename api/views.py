from rest_framework import viewsets, permissions, filters
from tenants.models import Tenant, TenantMembership, Category, Product, Order, OrderItem
from .serializers import (
    TenantSerializer, TenantMembershipSerializer, CategorySerializer,
    ProductSerializer, OrderSerializer
)

class TenantViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Tenants / Tiendas.
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        # Si no es staff ni superuser, solo ver tiendas activas
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para categorías, aisladas por tenant si se pasa ?tenant=<slug>
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_slug = self.request.query_params.get('tenant')
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
        return qs


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint para productos, con filtro por tenant ?tenant=<slug> o ?category=<slug>
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_slug = self.request.query_params.get('tenant')
        category_slug = self.request.query_params.get('category')
        
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
            
        # Si el usuario no es staff de esa tienda, solo mostrar activos
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
            
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint para órdenes/pedidos de tiendas.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_slug = self.request.query_params.get('tenant')
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
        return qs


class TenantMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint para roles y miembros de cada tenant.
    """
    queryset = TenantMembership.objects.all()
    serializer_class = TenantMembershipSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_slug = self.request.query_params.get('tenant')
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
        return qs
