from decimal import Decimal
from django.shortcuts import get_object_or_404
from .models import Tenant, TenantMembership, Category, Product

def get_tenant_or_404(slug):
    """Obtiene un tenant activo o lanza 404"""
    return get_object_or_404(Tenant, slug=slug)

def user_can_admin_tenant(user, tenant):
    """
    Verifica si un usuario tiene permisos de administrador sobre el tenant.
    El superusuario de Django tiene acceso global a todos los tenants.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return TenantMembership.objects.filter(
        tenant=tenant,
        user=user,
        role=TenantMembership.ROLE_ADMIN,
        is_active=True
    ).exists()

def user_can_staff_tenant(user, tenant):
    """Verifica si el usuario es admin o staff del tenant"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return TenantMembership.objects.filter(
        tenant=tenant,
        user=user,
        role__in=[TenantMembership.ROLE_ADMIN, TenantMembership.ROLE_STAFF],
        is_active=True
    ).exists()

# Helpers para el Carrito Aislado por Tenant
def get_cart_session_key(tenant_slug):
    return f"cart_{tenant_slug}"

def get_cart_data(request, tenant_slug):
    """Devuelve el diccionario del carrito para este tenant y sus totales calculados"""
    key = get_cart_session_key(tenant_slug)
    cart = request.session.get(key, {})
    
    items = []
    total_amount = Decimal('0.00')
    total_items = 0

    for prod_id, item in cart.items():
        qty = item.get('quantity', 1)
        price = Decimal(str(item.get('price', 0)))
        subtotal = price * qty
        total_amount += subtotal
        total_items += qty
        items.append({
            'product_id': prod_id,
            'name': item.get('name'),
            'price': price,
            'quantity': qty,
            'subtotal': subtotal,
            'image_url': item.get('image_url', ''),
        })

    return {
        'items': items,
        'total_amount': total_amount,
        'total_items': total_items,
        'raw_cart': cart
    }

def add_to_cart(request, tenant, product_id, quantity=1):
    key = get_cart_session_key(tenant.slug)
    cart = request.session.get(key, {})
    product = get_object_or_404(Product, id=product_id, tenant=tenant, is_active=True)

    prod_id_str = str(product.id)
    if prod_id_str in cart:
        cart[prod_id_str]['quantity'] += quantity
    else:
        cart[prod_id_str] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': quantity,
            'image_url': product.image_url or 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80',
        }
    
    request.session[key] = cart
    request.session.modified = True
    return cart

def update_cart_quantity(request, tenant_slug, product_id, quantity):
    key = get_cart_session_key(tenant_slug)
    cart = request.session.get(key, {})
    prod_id_str = str(product_id)

    if prod_id_str in cart:
        if quantity <= 0:
            del cart[prod_id_str]
        else:
            cart[prod_id_str]['quantity'] = quantity
        request.session[key] = cart
        request.session.modified = True
    return cart

def remove_from_cart(request, tenant_slug, product_id):
    key = get_cart_session_key(tenant_slug)
    cart = request.session.get(key, {})
    prod_id_str = str(product_id)
    if prod_id_str in cart:
        del cart[prod_id_str]
        request.session[key] = cart
        request.session.modified = True
    return cart

def clear_cart(request, tenant_slug):
    key = get_cart_session_key(tenant_slug)
    if key in request.session:
        del request.session[key]
        request.session.modified = True

def seed_tenant_sample_data(tenant, template_type="fashion"):
    """
    Crea categorías y productos de ejemplo para que la tienda creada
    tenga un aspecto profesional e interactivo inmediatamente.
    """
    if template_type == "tech":
        cat_audio, _ = Category.objects.get_or_create(tenant=tenant, name="Audio & Auriculares", slug="audio")
        cat_laptops, _ = Category.objects.get_or_create(tenant=tenant, name="Laptops & PC", slug="laptops")
        cat_gadgets, _ = Category.objects.get_or_create(tenant=tenant, name="Accesorios & Gadgets", slug="gadgets")

        products = [
            ("Auriculares Inalámbricos Pro Noise-Cancelling", cat_audio, 129.99, 15, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80", "Top Ventas"),
            ("Auriculares Studio Hi-Fi Bluetooth", cat_audio, 89.50, 20, "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&q=80", "Oferta"),
            ("Laptop Ultradelgada Pro 14' 16GB RAM", cat_laptops, 899.00, 8, "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&q=80", "Nuevo"),
            ("Smartwatch Serie 7 Deportivo Resistente al Agua", cat_gadgets, 199.90, 25, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80", "Destacado"),
            ("Teclado Mecánico RGB Switch Blue", cat_gadgets, 65.00, 30, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&q=80", "Recomendado"),
            ("Cámara Mirrorless 4K para Creadores", cat_gadgets, 650.00, 5, "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&q=80", "Premium"),
        ]
    elif template_type == "sneakers":
        cat_running, _ = Category.objects.get_or_create(tenant=tenant, name="Running & Sport", slug="running")
        cat_casual, _ = Category.objects.get_or_create(tenant=tenant, name="Sneakers Urbanas", slug="urbanas")
        cat_edition, _ = Category.objects.get_or_create(tenant=tenant, name="Ediciones Especiales", slug="ediciones")

        products = [
            ("Air Pulse Runner Max - Edición Tokio", cat_running, 149.99, 18, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80", "Top 1"),
            ("Urban Street Classic White Minimal", cat_casual, 95.00, 22, "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=600&q=80", "Popular"),
            ("Retro Heritage High-Top Basketball", cat_edition, 180.00, 10, "https://images.unsplash.com/photo-1552346154-21d32810aba3?w=600&q=80", "Limitado"),
            ("Vortex Speed Zoom Trail", cat_running, 120.00, 14, "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=600&q=80", "Nuevo"),
        ]
    else: # Fashion / Boutique default
        cat_ropa, _ = Category.objects.get_or_create(tenant=tenant, name="Ropa & Colección", slug="ropa")
        cat_acc, _ = Category.objects.get_or_create(tenant=tenant, name="Accesorios & Joyería", slug="accesorios")
        cat_calzado, _ = Category.objects.get_or_create(tenant=tenant, name="Calzado Elegante", slug="calzado")

        products = [
            ("Chaqueta Cuero Café Estilo Vintage", cat_ropa, 115.00, 12, "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&q=80", "Exclusivo"),
            ("Reloj Cronógrafo de Cuero Italiano", cat_acc, 175.00, 16, "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&q=80", "Destacado"),
            ("Gafas de Sol Polarizadas Aviador Oro", cat_acc, 69.90, 25, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&q=80", "Verano"),
            ("Mochila Urbana de Cuero y Lona", cat_ropa, 85.00, 20, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80", "Top Ventas"),
            ("Zapatos Oxford Clásicos Negros", cat_calzado, 130.00, 15, "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=600&q=80", "Elegante"),
        ]

    for name, cat, price, stock, img, badge in products:
        Product.objects.create(
            tenant=tenant,
            category=cat,
            name=name,
            price=price,
            stock=stock,
            image_url=img,
            badge=badge,
            description=f"Excelente producto {name}. Diseñado con materiales de la más alta calidad para la tienda {tenant.name}.",
            is_active=True
        )
