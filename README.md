# 🛒 Plataforma SaaS E-Commerce Multi-Tenant (Estilo Shopify)

Este proyecto implementa una plataforma de comercio electrónico multi-inquilino (**Multi-Tenant**) construida con **Django** y **Django REST Framework**, inspirada en la arquitectura de **Shopify**.

---

## 🌟 Características Principales

1. **🏬 Tiendas Autónomas e Independientes (Tenants)**:
   - Cada tienda opera con su propia URL identificadora: `/store/<slug>/`
   - Identidad visual personalizable: paleta de colores de marca, logotipo, banner, moneda y eslogan.
   - Catálogo propio de categorías y productos con gestión de inventario en tiempo real.

2. **🛍️ Carrito de Compras 100% Aislado**:
   - Cada tenant posee su propio carrito de compras independiente almacenado en sesión (`cart_<tenant_slug>`).
   - Un cliente puede agregar artículos en "Sneakers Hub" y en "TechNova Pro" sin que los productos se mezclen o interfieran entre sí.
   - Proceso de Checkout y confirmación de pedidos exclusivo para cada tienda.

3. **👑 Panel de Superusuario de la Plataforma (`/platform-admin/`)**:
   - Tablero central con KPIs globales (Tenants totales, activos, productos totales en el sistema y ventas acumuladas).
   - **Asistente de Creación de Tenants (Wizard)**:
     - Formulario intuitivo con generación automática de slug.
     - Creación instantánea de la cuenta del Administrador de la tienda.
     - **Plantillas de catálogo precargadas** (*Boutique de Moda*, *Tecnología*, *Zapatillas Urbanas* o *Vacío*) para comenzar a vender de inmediato.
   - Control de estado (activar, pausar o suspender tiendas).

4. **👔 Panel de Administración del Negocio (Tenant Admin - `/store/<slug>/admin/`)**:
   - Acceso protegido exclusivo: el admin de una tienda **no puede** acceder ni ver datos de otras tiendas.
   - **Gestión de Colaboradores y Usuarios**:
     - Crear nuevos usuarios asignados a la tienda.
     - Asignar roles: `Administrador del Tenant` o `Staff / Ventas`.
     - Editar nombres, correo, estado activo e incluso restablecer contraseñas.
   - **Gestión de Catálogo**: Crear, editar y eliminar productos con soporte de stock, insignias (oferta, nuevo, top) y fotos.
   - **Gestión de Pedidos**: Visualización de órdenes de clientes con selector de estado (*Pendiente, Pagado, En Preparación, Enviado, Entregado, Cancelado*).
   - **Configuración de Marca**: Ajuste interactivo del color primario, secundario, nombre y datos de contacto.

5. **🔌 API REST Completa (Django REST Framework)**:
   - Endpoints navegables en `/api/` para Tenants, Categorías, Productos y Pedidos, listos para aplicaciones móviles o frontend desacoplado.

6. **💾 Base de Datos SQLite con Migración Fácil a PostgreSQL**:
   - Desarrollado con el ORM estándar de Django, garantizando que el cambio a PostgreSQL o MySQL requiera únicamente configurar variables de entorno sin modificar una sola línea de código.

---

## 🚀 Inicio Rápido

### 1. Activar el Entorno Virtual
En Windows PowerShell:
```powershell
.\env\Scripts\activate
```

### 2. Ejecutar el Servidor
```powershell
.\env\Scripts\python.exe manage.py runserver
```
El servidor estará disponible en: **`http://127.0.0.1:8000/`**

---

## 🔑 Credenciales de Prueba Precargadas

| Rol | Usuario | Contraseña | Enlace |
| :--- | :--- | :--- | :--- |
| **SuperAdmin (Plataforma)** | `admin` | `admin123` | [Panel SuperAdmin](http://127.0.0.1:8000/platform-admin/) |
| **Admin Sneakers Hub** | `admin_sneakers` | `sneakers123` | [Admin Sneakers](http://127.0.0.1:8000/store/sneakers-hub/admin/) |
| **Admin TechNova Pro** | `admin_technova` | `tech123` | [Admin TechNova](http://127.0.0.1:8000/store/technova/admin/) |

---

## 🧭 Rutas Principales del Sistema

- **Página de Inicio / Landing**: `http://127.0.0.1:8000/`
- **Panel de SuperAdmin**: `http://127.0.0.1:8000/platform-admin/`
- **Tienda 1 (Sneakers Hub)**: `http://127.0.0.1:8000/store/sneakers-hub/`
- **Tienda 2 (TechNova Pro)**: `http://127.0.0.1:8000/store/technova/`
- **API REST**: `http://127.0.0.1:8000/api/`
- **Django Admin Oficial**: `http://127.0.0.1:8000/admin/`

---

## 🔄 Cómo Migrar de SQLite a PostgreSQL / MySQL

En `core/settings.py` el proyecto ya está preparado. Para conectar una base de datos PostgreSQL en producción, solo instala el driver y define las variables de entorno:

```powershell
# 1. Instalar conector de PostgreSQL
pip install psycopg2-binary

# 2. Configurar variables de entorno (en tu archivo .env o en el servidor)
$env:DB_ENGINE="postgresql"
$env:DB_NAME="mi_base_de_datos"
$env:DB_USER="mi_usuario"
$env:DB_PASSWORD="mi_password"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"

# 3. Aplicar migraciones
python manage.py migrate
```

---

## 🧪 Pruebas Automatizadas
Para verificar el funcionamiento y aislamiento de carritos y permisos:
```powershell
.\env\Scripts\python.exe test_platform.py
```
Todas las 7 pruebas pasan al 100%.
