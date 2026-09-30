from django.urls import path, include
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'tenants', views.TenantViewSet, basename='api-tenants')
router.register(r'categories', views.CategoryViewSet, basename='api-categories')
router.register(r'products', views.ProductViewSet, basename='api-products')
router.register(r'orders', views.OrderViewSet, basename='api-orders')
router.register(r'memberships', views.TenantMembershipViewSet, basename='api-memberships')

urlpatterns = [
    path('', include(router.urls)),
]
