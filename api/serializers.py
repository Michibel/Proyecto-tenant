from rest_framework import serializers
from django.contrib.auth.models import User
from tenants.models import Tenant, TenantMembership, Category, Product, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id']

class TenantMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = TenantMembership
        fields = ['id', 'tenant', 'user', 'user_id', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'tenant', 'name', 'slug', 'description', 'products_count', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    tenant_slug = serializers.ReadOnlyField(source='tenant.slug')

    class Meta:
        model = Product
        fields = [
            'id', 'tenant', 'tenant_name', 'tenant_slug', 'category', 'category_name',
            'name', 'slug', 'description', 'price', 'stock', 'image_url', 'badge',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'subtotal']
        read_only_fields = ['id']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'tenant', 'customer_name', 'customer_email', 'customer_phone',
            'shipping_address', 'order_notes', 'status', 'status_display',
            'total_amount', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TenantSerializer(serializers.ModelSerializer):
    total_products = serializers.ReadOnlyField()
    total_orders = serializers.ReadOnlyField()
    total_sales = serializers.ReadOnlyField()
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'description', 'primary_color', 'secondary_color',
            'logo_url', 'banner_url', 'contact_email', 'contact_phone', 'currency_symbol',
            'is_active', 'owner', 'owner_username', 'total_products', 'total_orders',
            'total_sales', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
