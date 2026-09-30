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

from django.test import Client
from django.contrib.auth.models import User
from tenants.models import Tenant, Product, Order, TenantMembership

def test_all():
    print("🧪 Ejecutando pruebas completas del sistema...")
    client = Client()

    # 1. Home page
    r = client.get('/')
    assert r.status_code == 200, f"Error en Home: {r.status_code}"
    print("✅ 1. Home de la plataforma responde 200 OK.")

    # 2. Storefronts
    r_sneakers = client.get('/store/sneakers-hub/')
    assert r_sneakers.status_code == 200, f"Error en storefront sneakers: {r_sneakers.status_code}"
    r_tech = client.get('/store/technova/')
    assert r_tech.status_code == 200, f"Error en storefront tech: {r_tech.status_code}"
    print("✅ 2. Storefronts de Sneakers Hub y TechNova Pro responden 200 OK.")

    # 3. Carrito Aislado por Tenant
    t_sneakers = Tenant.objects.get(slug='sneakers-hub')
    t_tech = Tenant.objects.get(slug='technova')
    p_sneakers = t_sneakers.products.first()
    p_tech = t_tech.products.first()

    # Agregar sneaker al carrito de sneakers-hub
    r_add1 = client.post(f'/store/sneakers-hub/cart/add/{p_sneakers.id}/', {'quantity': 2}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert r_add1.status_code == 200
    assert r_add1.json()['cart_total_items'] == 2

    # Agregar gadget al carrito de technova en la misma sesión de cliente
    r_add2 = client.post(f'/store/technova/cart/add/{p_tech.id}/', {'quantity': 3}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert r_add2.status_code == 200
    assert r_add2.json()['cart_total_items'] == 3

    # Verificar aislamiento de carritos en sesión
    session = client.session
    cart_sneakers = session.get('cart_sneakers-hub')
    cart_technova = session.get('cart_technova')

    assert str(p_sneakers.id) in cart_sneakers, "El producto de zapatillas debe estar en el carrito de sneakers"
    assert str(p_tech.id) not in cart_sneakers, "¡AISLAMIENTO FALLÓ! El producto de tech NO debe estar en sneakers"
    assert str(p_tech.id) in cart_technova, "El producto de tech debe estar en el carrito de technova"
    assert str(p_sneakers.id) not in cart_technova, "¡AISLAMIENTO FALLÓ! El producto de zapatillas NO debe estar en technova"
    print("✅ 3. Carritos de compra 100% aislados e independientes entre tenants verificado con éxito.")

    # 4. SuperAdmin Dashboard & Access
    admin_user = User.objects.get(username='admin')
    client.force_login(admin_user)
    r_super = client.get('/platform-admin/')
    assert r_super.status_code == 200, f"Superadmin dashboard status: {r_super.status_code}"
    print("✅ 4. Acceso del SuperAdmin a /platform-admin/ verificado 200 OK.")

    # 5. Seguridad y Aislamiento de Tenant Admin
    sneakers_admin = User.objects.get(username='admin_sneakers')
    client.force_login(sneakers_admin)
    
    # Puede entrar a su propio admin
    r_own = client.get('/store/sneakers-hub/admin/')
    assert r_own.status_code == 200, f"Error entrando a propio admin: {r_own.status_code}"

    # NO puede entrar al admin de otra tienda (TechNova) -> Debe devolver 403 Forbidden
    r_forbidden = client.get('/store/technova/admin/')
    assert r_forbidden.status_code == 403, f"Debe devolver 403 Forbidden para otra tienda, pero devolvió {r_forbidden.status_code}"
    print("✅ 5. Seguridad de Tenant Admin verificada (Admin de Sneakers no puede acceder a TechNova - 403 Forbidden).")

    # 6. Creación de usuario dentro del tenant
    r_create_user = client.post('/store/sneakers-hub/admin/users/create/', {
        'username': 'nuevo_vendedor',
        'email': 'vendedor@sneakers.com',
        'first_name': 'Pedro',
        'last_name': 'Soto',
        'role': 'STAFF',
        'password': 'vendedor_pass_123'
    })
    assert r_create_user.status_code in [302, 200]
    assert User.objects.filter(username='nuevo_vendedor').exists()
    assert TenantMembership.objects.filter(tenant=t_sneakers, user__username='nuevo_vendedor', role='STAFF').exists()
    print("✅ 6. Creación de usuarios y asignación de roles por parte del Tenant Admin verificada exitosamente.")

    # 7. Checkout de compra
    client.logout()
    # Agregar item
    client.post(f'/store/sneakers-hub/cart/add/{p_sneakers.id}/', {'quantity': 1})
    initial_stock = p_sneakers.stock
    r_checkout = client.post('/store/sneakers-hub/checkout/', {
        'customer_name': 'Cliente Prueba',
        'customer_email': 'cliente@test.com',
        'customer_phone': '+56 9 1122 3344',
        'shipping_address': 'Calle Falsa 123',
        'order_notes': 'Entregar en conserjería'
    })
    assert r_checkout.status_code == 302, f"Checkout redirect status: {r_checkout.status_code}"
    p_sneakers.refresh_from_db()
    assert p_sneakers.stock == initial_stock - 1, "El stock debe haberse descontado en 1"
    print("✅ 7. Checkout de compra, creación de orden atómica y descuento de stock verificado.")

    print("\n🎉 ¡TODAS LAS PRUEBAS (7/7) PASARON SATISFACTORIAMENTE!")

if __name__ == '__main__':
    test_all()
