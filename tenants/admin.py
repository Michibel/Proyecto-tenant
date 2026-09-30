from django.contrib import admin
from .models import Tenant, TenantMembership, Category, Product, Order, OrderItem

class TenantMembershipInline(admin.TabularInline):
    model = TenantMembership
    extra = 1

class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'price', 'stock', 'is_active')

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'owner', 'created_at')
    search_fields = ('name', 'slug', 'description')
    list_filter = ('is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TenantMembershipInline, ProductInline]

@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'tenant')
    search_fields = ('user__username', 'user__email', 'tenant__name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('name', 'slug', 'tenant__name')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'category', 'price', 'stock', 'is_active')
    list_filter = ('tenant', 'is_active', 'category')
    search_fields = ('name', 'description', 'tenant__name')
    prepopulated_fields = {'slug': ('name',)}

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'customer_name', 'customer_email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'tenant', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'tenant__name')
    inlines = [OrderItemInline]
