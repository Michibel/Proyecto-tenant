from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Tenant(models.Model):
    """
    Representa una tienda / tenant independiente (estilo Shopify).
    Cada tenant tiene su propio branding, catálogo, usuarios y pedidos.
    """
    name = models.CharField(max_length=150, help_text="Nombre comercial de la tienda")
    slug = models.SlugField(max_length=150, unique=True, help_text="Identificador único para la URL (ej: mi-tienda)")
    description = models.TextField(blank=True, default="", help_text="Descripción o lema de la tienda")
    
    # Personalización visual / Branding
    primary_color = models.CharField(max_length=20, default="#4F46E5", help_text="Color primario en formato HEX (ej: #4F46E5)")
    secondary_color = models.CharField(max_length=20, default="#06B6D4", help_text="Color secundario o de acento HEX")
    logo_url = models.CharField(max_length=500, blank=True, default="", help_text="URL o enlace del logo")
    banner_url = models.CharField(max_length=500, blank=True, default="", help_text="URL o enlace del banner principal")
    
    # Datos de contacto de la tienda
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")
    currency_symbol = models.CharField(max_length=10, default="$", help_text="Símbolo de moneda (ej: $, USD, €, CLP)")
    
    # Estado y Propietario
    is_active = models.BooleanField(default=True, help_text="Si la tienda está activa y accesible al público")
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="owned_tenants",
        help_text="Usuario propietario/creador principal"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tenant / Tienda'
        verbose_name_plural = 'Tenants / Tiendas'

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def total_products(self):
        return self.products.count()

    @property
    def total_orders(self):
        return self.orders.count()

    @property
    def total_sales(self):
        orders = self.orders.exclude(status='CANCELLED')
        return sum(order.total_amount for order in orders) or 0


class TenantMembership(models.Model):
    """
    Gestiona los roles y permisos de los usuarios dentro de un Tenant específico.
    Permite que cada tienda tenga su propio Administrador, Staff o Clientes registrados.
    """
    ROLE_ADMIN = 'ADMIN'
    ROLE_STAFF = 'STAFF'
    ROLE_CUSTOMER = 'CUSTOMER'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrador del Tenant'),
        (ROLE_STAFF, 'Staff / Vendedor'),
        (ROLE_CUSTOMER, 'Cliente Registrado'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'user')
        verbose_name = 'Membresía / Rol de Usuario en Tenant'
        verbose_name_plural = 'Membresías / Roles de Usuarios en Tenants'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} ({self.tenant.name})"

    @property
    def is_tenant_admin(self):
        return self.role == self.ROLE_ADMIN


class Category(models.Model):
    """
    Categoría de productos perteneciente a un Tenant específico.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'slug')
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.tenant.slug}]"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Producto del catálogo perteneciente de forma aislada a un Tenant.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=10)
    image_url = models.CharField(max_length=500, blank=True, default="", help_text="URL de la imagen del producto")
    badge = models.CharField(max_length=50, blank=True, default="", help_text="Ej: 'Nuevo', 'Oferta', 'Más Vendido'")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (${self.price}) - {self.tenant.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Pedido realizado dentro de un Tenant con su carrito de compra independiente.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_SHIPPED = 'SHIPPED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PAID, 'Pagado'),
        (STATUS_PROCESSING, 'En Preparación'),
        (STATUS_SHIPPED, 'Enviado'),
        (STATUS_DELIVERED, 'Entregado'),
        (STATUS_CANCELLED, 'Cancelado'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='orders')
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=50, blank=True, default="")
    shipping_address = models.TextField()
    order_notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido / Orden'
        verbose_name_plural = 'Pedidos / Órdenes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.id} - {self.customer_name} ({self.tenant.name}) - ${self.total_amount}"


class OrderItem(models.Model):
    """
    Detalle de ítems de una orden.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} (${self.subtotal})"
