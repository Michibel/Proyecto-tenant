from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.db.models import Sum, Count, Q

from .models import Tenant, TenantMembership, Category, Product, Order, OrderItem
from .forms import (
    TenantCreationForm, ProductForm, CategoryForm,
    TenantUserCreateForm, TenantUserEditForm, TenantSettingsForm, CheckoutForm
)
from .utils import (
    get_tenant_or_404, user_can_admin_tenant, user_can_staff_tenant,
    get_cart_data, add_to_cart, update_cart_quantity, remove_from_cart, clear_cart,
    seed_tenant_sample_data
)

# ==========================================
# VISTAS DE PLATAFORMA / SUPERADMIN / HOME
# ==========================================

def home_view(request):
    """Página de inicio global de la plataforma SaaS Multi-Tenant"""
    tenants = Tenant.objects.filter(is_active=True).annotate(
        products_total=Count('products')
    )
    all_tenants_count = Tenant.objects.count()
    total_products = Product.objects.count()
    total_sales = Order.objects.exclude(status='CANCELLED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'tenants': tenants,
        'all_tenants_count': all_tenants_count,
        'total_products': total_products,
        'total_sales': total_sales,
    }
    return render(request, 'platform/home.html', context)


def custom_login_view(request):
    """Login universal para superadministradores y administradores de tiendas"""
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido de vuelta, {user.username}!")
            
            # Si venía a una URL específica, redirigir
            if next_url:
                return redirect(next_url)
                
            # Si es superusuario, llevar al panel de superusuario
            if user.is_superuser:
                return redirect('superadmin_dashboard')
                
            # Si administra algún tenant, llevar al primer tenant que administre
            membership = TenantMembership.objects.filter(user=user, role=TenantMembership.ROLE_ADMIN, is_active=True).first()
            if membership:
                return redirect('tenant_admin_dashboard', slug=membership.tenant.slug)
                
            return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña inválidos.")
    else:
        form = AuthenticationForm()

    return render(request, 'platform/login.html', {'form': form, 'next': next_url})


def custom_logout_view(request):
    """Cerrar sesión de forma segura"""
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('home')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def superadmin_dashboard(request):
    """
    Panel de Control del Superusuario:
    Administra todos los tenants, estadísticas globales y asistente de creación.
    """
    tenants = Tenant.objects.all().order_by('-created_at')
    
    # Métricas Globales
    total_tenants = tenants.count()
    active_tenants = tenants.filter(is_active=True).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.exclude(status='CANCELLED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_users = User.objects.count()

    form = TenantCreationForm()

    context = {
        'tenants': tenants,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'form': form,
    }
    return render(request, 'superadmin/dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def superadmin_tenant_create(request):
    """Creación de un nuevo Tenant con su administrador y catálogo inicial"""
    if request.method == 'POST':
        form = TenantCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                tenant = form.save(commit=False)
                
                # Crear o vincular usuario administrador del tenant
                admin_username = form.cleaned_data['admin_username']
                admin_email = form.cleaned_data['admin_email']
                admin_password = form.cleaned_data['admin_password']
                catalog_template = form.cleaned_data['catalog_template']

                user, created = User.objects.get_or_create(
                    username=admin_username,
                    defaults={'email': admin_email, 'is_staff': True}
                )
                if created:
                    user.set_password(admin_password)
                    user.save()
                else:
                    user.email = admin_email
                    user.is_staff = True
                    user.save()

                tenant.owner = user
                tenant.save()

                # Crear membresía de ADMIN para este tenant
                TenantMembership.objects.get_or_create(
                    tenant=tenant,
                    user=user,
                    defaults={'role': TenantMembership.ROLE_ADMIN, 'is_active': True}
                )

                # Sembrar catálogo de muestra si se seleccionó
                if catalog_template != 'empty':
                    seed_tenant_sample_data(tenant, template_type=catalog_template)

            messages.success(request, f"¡Tienda '{tenant.name}' creada exitosamente con el administrador '{user.username}'!")
            return redirect('superadmin_dashboard')
        else:
            messages.error(request, "Por favor revisa los errores en el formulario.")
            tenants = Tenant.objects.all().order_by('-created_at')
            return render(request, 'superadmin/dashboard.html', {'form': form, 'tenants': tenants})
    return redirect('superadmin_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def superadmin_tenant_toggle(request, slug):
    """Activar / Suspender un tenant"""
    tenant = get_object_or_404(Tenant, slug=slug)
    tenant.is_active = not tenant.is_active
    tenant.save()
    status_str = "activada" if tenant.is_active else "suspendida"
    messages.info(request, f"La tienda '{tenant.name}' ha sido {status_str}.")
    return redirect('superadmin_dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def superadmin_tenant_delete(request, slug):
    """Eliminar un tenant de la plataforma"""
    tenant = get_object_or_404(Tenant, slug=slug)
    tenant_name = tenant.name
    tenant.delete()
    messages.warning(request, f"La tienda '{tenant_name}' y todos sus datos han sido eliminados.")
    return redirect('superadmin_dashboard')


# ==========================================
# STOREFRONT DE TENANT & CARRITO AISLADO
# ==========================================

def storefront_view(request, slug):
    """Página de inicio pública de la tienda del Tenant (Shopify-like)"""
    tenant = get_object_or_404(Tenant, slug=slug)
    if not tenant.is_active and not (request.user.is_authenticated and user_can_admin_tenant(request.user, tenant)):
        return render(request, 'storefront/inactive.html', {'tenant': tenant}, status=403)

    categories = tenant.categories.all()
    products_qs = tenant.products.filter(is_active=True)

    # Filtros por categoría y búsqueda
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')

    current_category = None
    if category_slug:
        current_category = tenant.categories.filter(slug=category_slug).first()
        if current_category:
            products_qs = products_qs.filter(category=current_category)

    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    cart_data = get_cart_data(request, tenant.slug)

    context = {
        'tenant': tenant,
        'categories': categories,
        'products': products_qs,
        'current_category': current_category,
        'search_query': search_query,
        'cart': cart_data,
        'user_is_admin': user_can_admin_tenant(request.user, tenant),
    }
    return render(request, 'storefront/index.html', context)


def storefront_product_detail(request, slug, product_slug):
    """Detalle de producto en la tienda"""
    tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
    product = get_object_or_404(Product, tenant=tenant, slug=product_slug, is_active=True)
    related_products = tenant.products.filter(is_active=True).exclude(id=product.id)[:4]
    cart_data = get_cart_data(request, tenant.slug)

    context = {
        'tenant': tenant,
        'product': product,
        'related_products': related_products,
        'cart': cart_data,
    }
    return render(request, 'storefront/product_detail.html', context)


def cart_view(request, slug):
    """Vista completa del carrito de compras independiente para este tenant"""
    tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
    cart_data = get_cart_data(request, tenant.slug)

    context = {
        'tenant': tenant,
        'cart': cart_data,
    }
    return render(request, 'storefront/cart.html', context)


def cart_add_view(request, slug, product_id):
    """Añadir ítem al carrito aislado del tenant (soporta AJAX o POST tradicional)"""
    tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
    qty = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1
    
    add_to_cart(request, tenant, product_id, quantity=qty)
    cart_data = get_cart_data(request, tenant.slug)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'message': 'Producto añadido al carrito',
            'cart_total_items': cart_data['total_items'],
            'cart_total_amount': str(cart_data['total_amount']),
        })
    
    messages.success(request, "Producto añadido a tu carrito.")
    return redirect(request.META.get('HTTP_REFERER', f'/store/{tenant.slug}/'))


def cart_update_view(request, slug, product_id):
    """Actualizar cantidad de un producto en el carrito"""
    tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        update_cart_quantity(request, tenant.slug, product_id, qty)
        cart_data = get_cart_data(request, tenant.slug)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_total_items': cart_data['total_items'],
                'cart_total_amount': str(cart_data['total_amount']),
            })
    return redirect('cart_view', slug=tenant.slug)


def cart_remove_view(request, slug, product_id):
    """Eliminar ítem del carrito del tenant"""
    tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
    remove_from_cart(request, tenant.slug, product_id)
    messages.info(request, "Producto eliminado de tu carrito.")
    return redirect('cart_view', slug=tenant.slug)


def checkout_view(request, slug):
    """Proceso de Checkout de la tienda del Tenant"""
    tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
    cart_data = get_cart_data(request, tenant.slug)

    if not cart_data['items']:
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de pagar.")
        return redirect('storefront_view', slug=tenant.slug)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.tenant = tenant
                order.total_amount = cart_data['total_amount']
                order.status = Order.STATUS_PENDING
                order.save()

                for item in cart_data['items']:
                    product = Product.objects.filter(id=item['product_id'], tenant=tenant).first()
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=item['name'],
                        price=item['price'],
                        quantity=item['quantity'],
                        subtotal=item['subtotal']
                    )
                    # Reducir stock si existe producto
                    if product and product.stock >= item['quantity']:
                        product.stock -= item['quantity']
                        product.save()

                # Limpiar únicamente el carrito de esta tienda
                clear_cart(request, tenant.slug)

            messages.success(request, f"¡Gracias por tu compra! Tu pedido #{order.id} ha sido registrado.")
            return redirect('order_success_view', slug=tenant.slug, order_id=order.id)
    else:
        form = CheckoutForm()

    context = {
        'tenant': tenant,
        'cart': cart_data,
        'form': form,
    }
    return render(request, 'storefront/checkout.html', context)


def order_success_view(request, slug, order_id):
    """Página de confirmación de pedido recibido"""
    tenant = get_object_or_404(Tenant, slug=slug)
    order = get_object_or_404(Order, id=order_id, tenant=tenant)
    return render(request, 'storefront/order_success.html', {'tenant': tenant, 'order': order})


# ==========================================
# PANEL DE ADMINISTRACIÓN DEL TENANT
# ==========================================

def tenant_admin_required(view_func):
    """Decorador para proteger vistas del Tenant Admin"""
    def _wrapped(request, slug, *args, **kwargs):
        tenant = get_object_or_404(Tenant, slug=slug)
        if not user_can_admin_tenant(request.user, tenant):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next=/store/{slug}/admin/")
            return render(request, 'tenant_admin/forbidden.html', {'tenant': tenant}, status=403)
        return view_func(request, tenant, *args, **kwargs)
    return _wrapped


@tenant_admin_required
def tenant_admin_dashboard(request, tenant):
    """Dashboard general del Administrador de la Tienda"""
    products_count = tenant.products.count()
    orders_qs = tenant.orders.all()
    orders_count = orders_qs.count()
    pending_orders = orders_qs.filter(status='PENDING').count()
    total_sales = tenant.total_sales
    users_count = tenant.memberships.count()

    recent_orders = orders_qs.order_by('-created_at')[:5]
    low_stock_products = tenant.products.filter(stock__lte=5, is_active=True)[:5]

    context = {
        'tenant': tenant,
        'products_count': products_count,
        'orders_count': orders_count,
        'pending_orders': pending_orders,
        'total_sales': total_sales,
        'users_count': users_count,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'active_tab': 'dashboard',
    }
    return render(request, 'tenant_admin/dashboard.html', context)


@tenant_admin_required
def tenant_admin_products(request, tenant):
    """Listado y gestión de productos del tenant"""
    products = tenant.products.select_related('category').all()
    categories = tenant.categories.all()
    form = ProductForm(tenant=tenant)

    context = {
        'tenant': tenant,
        'products': products,
        'categories': categories,
        'form': form,
        'active_tab': 'products',
    }
    return render(request, 'tenant_admin/products.html', context)


@tenant_admin_required
def tenant_admin_product_create(request, tenant):
    """Crear un nuevo producto en el catálogo del tenant"""
    if request.method == 'POST':
        form = ProductForm(request.POST, tenant=tenant)
        if form.is_valid():
            product = form.save(commit=False)
            product.tenant = tenant
            product.save()
            messages.success(request, f"Producto '{product.name}' añadido exitosamente.")
            return redirect('tenant_admin_products', slug=tenant.slug)
    else:
        form = ProductForm(tenant=tenant)
    return render(request, 'tenant_admin/product_form.html', {'tenant': tenant, 'form': form, 'title': 'Nuevo Producto', 'active_tab': 'products'})


@tenant_admin_required
def tenant_admin_product_edit(request, tenant, product_id):
    """Editar un producto del tenant"""
    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto '{product.name}' actualizado.")
            return redirect('tenant_admin_products', slug=tenant.slug)
    else:
        form = ProductForm(instance=product, tenant=tenant)
    return render(request, 'tenant_admin/product_form.html', {'tenant': tenant, 'form': form, 'product': product, 'title': f'Editar: {product.name}', 'active_tab': 'products'})


@tenant_admin_required
def tenant_admin_product_delete(request, tenant, product_id):
    """Eliminar un producto"""
    product = get_object_or_404(Product, id=product_id, tenant=tenant)
    product_name = product.name
    product.delete()
    messages.warning(request, f"Producto '{product_name}' eliminado.")
    return redirect('tenant_admin_products', slug=tenant.slug)


@tenant_admin_required
def tenant_admin_categories(request, tenant):
    """Gestionar categorías de la tienda"""
    categories = tenant.categories.annotate(prod_count=Count('products')).all()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.tenant = tenant
            cat.save()
            messages.success(request, f"Categoría '{cat.name}' creada.")
            return redirect('tenant_admin_categories', slug=tenant.slug)
    else:
        form = CategoryForm()

    context = {
        'tenant': tenant,
        'categories': categories,
        'form': form,
        'active_tab': 'categories',
    }
    return render(request, 'tenant_admin/categories.html', context)


@tenant_admin_required
def tenant_admin_category_delete(request, tenant, category_id):
    """Eliminar una categoría"""
    cat = get_object_or_404(Category, id=category_id, tenant=tenant)
    cat.delete()
    messages.info(request, "Categoría eliminada.")
    return redirect('tenant_admin_categories', slug=tenant.slug)


@tenant_admin_required
def tenant_admin_orders(request, tenant):
    """Gestionar todos los pedidos de la tienda"""
    status_filter = request.GET.get('status')
    orders = tenant.orders.all()
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'tenant': tenant,
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
        'active_tab': 'orders',
    }
    return render(request, 'tenant_admin/orders.html', context)


@tenant_admin_required
def tenant_admin_order_detail(request, tenant, order_id):
    """Ver y cambiar estado de un pedido específico"""
    order = get_object_or_404(Order, id=order_id, tenant=tenant)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Estado del pedido actualizado a {order.get_status_display()}.")
            return redirect('tenant_admin_order_detail', slug=tenant.slug, order_id=order.id)

    context = {
        'tenant': tenant,
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'active_tab': 'orders',
    }
    return render(request, 'tenant_admin/order_detail.html', context)


@tenant_admin_required
def tenant_admin_users(request, tenant):
    """
    Gestión de usuarios del Tenant:
    El Admin del negocio puede ver sus colaboradores, crear usuarios, asignar roles y resetear contraseñas.
    """
    memberships = tenant.memberships.select_related('user').all()
    form = TenantUserCreateForm()

    context = {
        'tenant': tenant,
        'memberships': memberships,
        'form': form,
        'active_tab': 'users',
    }
    return render(request, 'tenant_admin/users.html', context)


@tenant_admin_required
def tenant_admin_user_create(request, tenant):
    """Crear un nuevo usuario dentro de este tenant"""
    if request.method == 'POST':
        form = TenantUserCreateForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            role = form.cleaned_data['role']
            password = form.cleaned_data['password']

            if User.objects.filter(username=username).exists():
                messages.error(request, f"El nombre de usuario '{username}' ya está en uso.")
                return redirect('tenant_admin_users', slug=tenant.slug)

            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    is_staff=True if role == TenantMembership.ROLE_ADMIN else False
                )
                TenantMembership.objects.create(
                    tenant=tenant,
                    user=user,
                    role=role,
                    is_active=True
                )
            messages.success(request, f"Usuario '{username}' creado exitosamente con rol {role}.")
            return redirect('tenant_admin_users', slug=tenant.slug)
    return redirect('tenant_admin_users', slug=tenant.slug)


@tenant_admin_required
def tenant_admin_user_edit(request, tenant, membership_id):
    """Editar información y rol de un usuario del tenant"""
    membership = get_object_or_404(TenantMembership, id=membership_id, tenant=tenant)
    target_user = membership.user

    if request.method == 'POST':
        form = TenantUserEditForm(request.POST)
        if form.is_valid():
            target_user.first_name = form.cleaned_data['first_name']
            target_user.last_name = form.cleaned_data['last_name']
            target_user.email = form.cleaned_data['email']
            target_user.save()

            membership.role = form.cleaned_data['role']
            membership.is_active = form.cleaned_data['is_active']
            membership.save()

            messages.success(request, f"Datos de '{target_user.username}' actualizados.")
            return redirect('tenant_admin_users', slug=tenant.slug)
    else:
        form = TenantUserEditForm(initial={
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'email': target_user.email,
            'role': membership.role,
            'is_active': membership.is_active,
        })

    context = {
        'tenant': tenant,
        'membership': membership,
        'target_user': target_user,
        'form': form,
        'active_tab': 'users',
    }
    return render(request, 'tenant_admin/user_edit.html', context)


@tenant_admin_required
def tenant_admin_user_password(request, tenant, membership_id):
    """Cambiar/resetear contraseña de un usuario del tenant"""
    membership = get_object_or_404(TenantMembership, id=membership_id, tenant=tenant)
    target_user = membership.user

    if request.method == 'POST':
        form = SetPasswordForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contraseña actualizada para {target_user.username}.")
            return redirect('tenant_admin_users', slug=tenant.slug)
    else:
        form = SetPasswordForm(target_user)

    context = {
        'tenant': tenant,
        'target_user': target_user,
        'form': form,
        'active_tab': 'users',
    }
    return render(request, 'tenant_admin/user_password.html', context)


@tenant_admin_required
def tenant_admin_user_delete(request, tenant, membership_id):
    """Quitar un usuario del tenant"""
    membership = get_object_or_404(TenantMembership, id=membership_id, tenant=tenant)
    if membership.user == request.user:
        messages.error(request, "No puedes eliminar tu propia membresía de administrador.")
        return redirect('tenant_admin_users', slug=tenant.slug)

    username = membership.user.username
    membership.delete()
    messages.info(request, f"El usuario '{username}' ha sido removido de la tienda.")
    return redirect('tenant_admin_users', slug=tenant.slug)


@tenant_admin_required
def tenant_admin_settings(request, tenant):
    """Personalizar marca, colores, nombre y contacto de la tienda"""
    if request.method == 'POST':
        form = TenantSettingsForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración e imagen de marca guardadas correctamente.")
            return redirect('tenant_admin_settings', slug=tenant.slug)
    else:
        form = TenantSettingsForm(instance=tenant)

    context = {
        'tenant': tenant,
        'form': form,
        'active_tab': 'settings',
    }
    return render(request, 'tenant_admin/settings.html', context)
