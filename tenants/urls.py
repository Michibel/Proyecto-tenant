from django.urls import path
from . import views

urlpatterns = [
    # Plataforma y Autenticación
    path('', views.home_view, name='home'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),

    # SuperAdmin de la Plataforma
    path('platform-admin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('platform-admin/tenant/create/', views.superadmin_tenant_create, name='superadmin_tenant_create'),
    path('platform-admin/tenant/<slug:slug>/toggle/', views.superadmin_tenant_toggle, name='superadmin_tenant_toggle'),
    path('platform-admin/tenant/<slug:slug>/delete/', views.superadmin_tenant_delete, name='superadmin_tenant_delete'),

    # Storefront Público del Tenant (Shopify-like)
    path('store/<slug:slug>/', views.storefront_view, name='storefront_view'),
    path('store/<slug:slug>/product/<slug:product_slug>/', views.storefront_product_detail, name='storefront_product_detail'),
    path('store/<slug:slug>/cart/', views.cart_view, name='cart_view'),
    path('store/<slug:slug>/cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('store/<slug:slug>/cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('store/<slug:slug>/cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('store/<slug:slug>/checkout/', views.checkout_view, name='checkout_view'),
    path('store/<slug:slug>/order-success/<int:order_id>/', views.order_success_view, name='order_success_view'),

    # Panel de Administración del Negocio (Tenant Admin)
    path('store/<slug:slug>/admin/', views.tenant_admin_dashboard, name='tenant_admin_dashboard'),
    path('store/<slug:slug>/admin/products/', views.tenant_admin_products, name='tenant_admin_products'),
    path('store/<slug:slug>/admin/products/create/', views.tenant_admin_product_create, name='tenant_admin_product_create'),
    path('store/<slug:slug>/admin/products/<int:product_id>/edit/', views.tenant_admin_product_edit, name='tenant_admin_product_edit'),
    path('store/<slug:slug>/admin/products/<int:product_id>/delete/', views.tenant_admin_product_delete, name='tenant_admin_product_delete'),
    
    path('store/<slug:slug>/admin/categories/', views.tenant_admin_categories, name='tenant_admin_categories'),
    path('store/<slug:slug>/admin/categories/<int:category_id>/delete/', views.tenant_admin_category_delete, name='tenant_admin_category_delete'),
    
    path('store/<slug:slug>/admin/orders/', views.tenant_admin_orders, name='tenant_admin_orders'),
    path('store/<slug:slug>/admin/orders/<int:order_id>/', views.tenant_admin_order_detail, name='tenant_admin_order_detail'),

    # Gestión de Usuarios del Negocio
    path('store/<slug:slug>/admin/users/', views.tenant_admin_users, name='tenant_admin_users'),
    path('store/<slug:slug>/admin/users/create/', views.tenant_admin_user_create, name='tenant_admin_user_create'),
    path('store/<slug:slug>/admin/users/<int:membership_id>/edit/', views.tenant_admin_user_edit, name='tenant_admin_user_edit'),
    path('store/<slug:slug>/admin/users/<int:membership_id>/password/', views.tenant_admin_user_password, name='tenant_admin_user_password'),
    path('store/<slug:slug>/admin/users/<int:membership_id>/delete/', views.tenant_admin_user_delete, name='tenant_admin_user_delete'),

    # Configuración de Marca del Tenant
    path('store/<slug:slug>/admin/settings/', views.tenant_admin_settings, name='tenant_admin_settings'),
]
