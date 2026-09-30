import os
import sys
import django

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from tenants.models import Tenant, TenantMembership, Category, Product, Order, OrderItem
from tenants.utils import seed_tenant_sample_data

def run_seed():
    print("🌱 Iniciando inicialización de datos de prueba...")

    # 1. Superusuario de la plataforma
    superuser, created = User.objects.get_or_create(username='admin')
    if created:
        superuser.set_password('admin123')
        superuser.email = 'admin@platform.com'
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save()
        print("✅ Superusuario creado: admin / admin123")
    else:
        print("ℹ️ Superusuario 'admin' ya existe")

    # 2. Tenant 1: Sneakers Hub
    t1_admin, _ = User.objects.get_or_create(username='admin_sneakers', defaults={'email': 'contacto@sneakershub.com', 'is_staff': True})
    t1_admin.set_password('sneakers123')
    t1_admin.first_name = 'Carlos'
    t1_admin.last_name = 'Mendoza'
    t1_admin.save()

    t1, created_t1 = Tenant.objects.get_or_create(
        slug='sneakers-hub',
        defaults={
            'name': 'Sneakers Hub',
            'description': 'Tienda de calzado urbano y deportivo con las marcas más exclusivas del mercado.',
            'primary_color': '#4F46E5', # Indigo
            'secondary_color': '#818CF8',
            'currency_symbol': '$',
            'contact_email': 'ventas@sneakershub.com',
            'contact_phone': '+56 9 8888 1111',
            'is_active': True,
            'owner': t1_admin
        }
    )

    TenantMembership.objects.get_or_create(
        tenant=t1,
        user=t1_admin,
        defaults={'role': TenantMembership.ROLE_ADMIN, 'is_active': True}
    )

    # Colaborador de Staff para Tenant 1
    t1_staff, _ = User.objects.get_or_create(username='vendedor_carlos', defaults={'email': 'carlos@sneakershub.com'})
    t1_staff.set_password('staff123')
    t1_staff.save()
    TenantMembership.objects.get_or_create(
        tenant=t1,
        user=t1_staff,
        defaults={'role': TenantMembership.ROLE_STAFF, 'is_active': True}
    )

    if created_t1:
        seed_tenant_sample_data(t1, template_type='sneakers')
        print("✅ Tienda 1 'Sneakers Hub' creada con catálogo de zapatillas.")

        # Crear orden de prueba para Tenant 1
        p1 = t1.products.first()
        if p1:
            order1 = Order.objects.create(
                tenant=t1,
                customer_name='Valentina Gómez',
                customer_email='valen@gmail.com',
                customer_phone='+56 9 4433 2211',
                shipping_address='Av. Providencia 1234, Depto 402, Santiago',
                status=Order.STATUS_PAID,
                total_amount=p1.price
            )
            OrderItem.objects.create(
                order=order1,
                product=p1,
                product_name=p1.name,
                price=p1.price,
                quantity=1,
                subtotal=p1.price
            )

    # 3. Tenant 2: TechNova Store
    t2_admin, _ = User.objects.get_or_create(username='admin_technova', defaults={'email': 'admin@technova.io', 'is_staff': True})
    t2_admin.set_password('tech123')
    t2_admin.first_name = 'Sofía'
    t2_admin.last_name = 'Herrera'
    t2_admin.save()

    t2, created_t2 = Tenant.objects.get_or_create(
        slug='technova',
        defaults={
            'name': 'TechNova Pro',
            'description': 'Tecnología de última generación, computadores de alto rendimiento y audio profesional.',
            'primary_color': '#059669', # Emerald Green
            'secondary_color': '#10B981',
            'currency_symbol': '$',
            'contact_email': 'soporte@technova.io',
            'contact_phone': '+56 9 7777 2222',
            'is_active': True,
            'owner': t2_admin
        }
    )

    TenantMembership.objects.get_or_create(
        tenant=t2,
        user=t2_admin,
        defaults={'role': TenantMembership.ROLE_ADMIN, 'is_active': True}
    )

    if created_t2:
        seed_tenant_sample_data(t2, template_type='tech')
        print("✅ Tienda 2 'TechNova Pro' creada con catálogo tecnológico.")

        # Crear orden de prueba para Tenant 2
        p2 = t2.products.first()
        if p2:
            order2 = Order.objects.create(
                tenant=t2,
                customer_name='Esteban Morales',
                customer_email='esteban@empresa.com',
                customer_phone='+56 9 9988 7766',
                shipping_address='Calle Los Leones 560, Providencia',
                status=Order.STATUS_PROCESSING,
                total_amount=p2.price
            )
            OrderItem.objects.create(
                order=order2,
                product=p2,
                product_name=p2.name,
                price=p2.price,
                quantity=1,
                subtotal=p2.price
            )

    print("\n🎉 Inicialización completada con éxito:")
    print("--------------------------------------------------")
    print("👑 SUPERADMIN DE LA PLATAFORMA:")
    print("   Usuario: admin")
    print("   Clave:   admin123")
    print("   URL:     http://127.0.0.1:8000/platform-admin/")
    print("")
    print("👟 TENANT 1: Sneakers Hub")
    print("   Storefront:  http://127.0.0.1:8000/store/sneakers-hub/")
    print("   Admin Panel: http://127.0.0.1:8000/store/sneakers-hub/admin/")
    print("   Admin User:  admin_sneakers / sneakers123")
    print("")
    print("💻 TENANT 2: TechNova Pro")
    print("   Storefront:  http://127.0.0.1:8000/store/technova/")
    print("   Admin Panel: http://127.0.0.1:8000/store/technova/admin/")
    print("   Admin User:  admin_technova / tech123")
    print("--------------------------------------------------")

if __name__ == '__main__':
    run_seed()
