from django import forms
from django.contrib.auth.models import User
from .models import Tenant, TenantMembership, Category, Product, Order

class TenantCreationForm(forms.ModelForm):
    """
    Formulario del Superusuario para crear una nueva tienda tenant,
    junto con la cuenta de su administrador inicial y opción de catálogo de muestra.
    """
    admin_username = forms.CharField(
        max_length=150, 
        label="Usuario del Administrador de la Tienda",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'ej: admin_zapateria'})
    )
    admin_email = forms.EmailField(
        label="Correo del Administrador",
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'admin@tienda.com'})
    )
    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': '••••••••'}),
        label="Contraseña inicial"
    )
    catalog_template = forms.ChoiceField(
        choices=[
            ('fashion', 'Boutique de Moda & Accesorios'),
            ('tech', 'Tecnología & Gadgets'),
            ('sneakers', 'Zapatillas & Calzado Urbano'),
            ('empty', 'Comenzar con catálogo vacío'),
        ],
        initial='fashion',
        label="Plantilla de Catálogo Inicial",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'description', 'primary_color', 'secondary_color', 'currency_symbol', 'contact_email', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'ej: Sneakers King'}),
            'slug': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'ej: sneakers-king'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'rows': 3, 'placeholder': 'Breve descripción de la tienda...'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-24 p-1 border rounded-lg cursor-pointer'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-24 p-1 border rounded-lg cursor-pointer'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': '$'}),
            'contact_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'contacto@tienda.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': '+56 9 1234 5678'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'stock', 'image_url', 'badge', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'https://images.unsplash.com/...'}),
            'badge': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Nuevo, Oferta, Top...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = Category.objects.filter(tenant=tenant)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'rows': 2}),
        }


class TenantUserCreateForm(forms.Form):
    """
    Permite al Admin de la tienda crear nuevos usuarios con roles (Admin, Staff/Vendedor).
    """
    username = forms.CharField(
        max_length=150,
        label="Nombre de Usuario",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'ej: juan_ventas'})
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'juan@tienda.com'})
    )
    first_name = forms.CharField(
        max_length=100, required=False,
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    last_name = forms.CharField(
        max_length=100, required=False,
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    role = forms.ChoiceField(
        choices=TenantMembership.ROLE_CHOICES,
        label="Rol en el Negocio",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
        label="Contraseña"
    )


class TenantUserEditForm(forms.Form):
    """
    Permite al Admin de la tienda modificar los datos y el rol de un usuario existente en su tienda.
    """
    first_name = forms.CharField(
        max_length=100, required=False,
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    last_name = forms.CharField(
        max_length=100, required=False,
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    role = forms.ChoiceField(
        choices=TenantMembership.ROLE_CHOICES,
        label="Rol en el Negocio",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'})
    )
    is_active = forms.BooleanField(
        required=False,
        label="Acceso Activo a la Tienda",
        widget=forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500'})
    )


class TenantSettingsForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'description', 'primary_color', 'secondary_color', 'currency_symbol', 'contact_email', 'contact_phone', 'logo_url', 'banner_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'rows': 3}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-24 p-1 border rounded-lg cursor-pointer'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-24 p-1 border rounded-lg cursor-pointer'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'contact_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'contact_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'logo_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'banner_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500'}),
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'shipping_address', 'order_notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Juan Pérez'}),
            'customer_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'juan@correo.com'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': '+56 9 8765 4321'}),
            'shipping_address': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'rows': 3, 'placeholder': 'Calle, Número, Depto, Ciudad'}),
            'order_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500', 'rows': 2, 'placeholder': 'Instrucciones opcionales para la entrega...'}),
        }
