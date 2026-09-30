from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin oficial
    path('admin/', admin.site.urls),
    
    # API REST (Django Rest Framework)
    path('api/', include('api.urls')),
    
    # Plataforma Multi-Tenant, Tiendas y Paneles
    path('', include('tenants.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
