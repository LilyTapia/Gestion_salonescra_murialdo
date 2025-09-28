# Gestión de Biblioteca (Django + MySQL)

Sistema de gestión de reservas de salones para biblioteca con API REST y interfaz web.

## Requisitos
- Python 3.10+
- MySQL 8
- `pip install -r requirements.txt`

## Configuración
1. Copia `.env.example` a `.env` y configura las variables de entorno:
   ```bash
   DJANGO_SECRET_KEY=tu_clave_secreta_aqui
   DJANGO_DEBUG=1
   DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
   DB_NAME=gestion_biblioteca
   DB_USER=root
   DB_PASSWORD=tu_clave
   DB_HOST=127.0.0.1
   DB_PORT=3306
   TIME_ZONE=America/Santiago
   ```
2. Crear entorno virtual e instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Inicialización
```bash
python manage.py migrate
python manage.py create_sample_users     # admin/admin1234 y docentes ana/bruno/carla (docente123)
python manage.py seed_data               # crea salones A/B/C y materiales con stock
python manage.py load_holidays --year 2025
python manage.py runserver               # http://127.0.0.1:8000
```

## API REST
- **Documentación**: `/api/docs/` (Swagger/OpenAPI)
- **Autenticación**: `POST /api/token/` (JWT) o Session Auth
- **Endpoints principales**:
  - `/api/rooms/` - Gestión de salones
  - `/api/materials/` - Materiales disponibles
  - `/api/inventory/` - Control de inventario
  - `/api/reservations/` - Reservas de salones
  - `/api/blackouts/` - Bloqueos de fechas (solo admin)

## Interfaz Web
- **Inicio**: `GET /` — Vista de salones e inventario con banner si hay bloqueo global
- **Reservas**: `GET/POST /reservas/nueva/` — Crear nueva reserva
- **Blackouts**: `GET /bloqueos/` — Gestión de bloqueos (solo administradores)
- **Admin Django**: `/admin/` — Panel administrativo completo

## Sistema de Permisos
- **Administrador**: `is_staff=True` o miembro del grupo `AdminBiblioteca`
  - Acceso completo a blackouts y gestión del sistema
- **Docente**: Usuario regular autenticado
  - Puede crear, editar y eliminar **solo sus propias** reservas
  - API aplica permiso `IsOwnerOrReadOnly`

## Reglas de Negocio
- **Horario permitido**: Lunes a Viernes, 08:00 - 18:00
- **Gestión de inventario**: Automática al crear/editar/eliminar reservas
- **Zona horaria**: America/Santiago (configurada en settings)

---

## Despliegue con Docker

### 1) Variables de entorno
El archivo `.env.docker` está preconfigurado con:
```bash
DJANGO_SECRET_KEY=super-secret-key-change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=America/Santiago
DB_NAME=gestion_biblioteca
DB_USER=root
DB_PASSWORD=Ene0208.
DB_HOST=db  # Nombre del servicio Docker
DB_PORT=3306
```

### 2) Levantar los servicios
```bash
docker compose up --build
```

### 3) Inicialización (primera vez)
Después de que los contenedores estén ejecutándose, configura la aplicación:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py create_sample_users
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py load_holidays --year 2025
```

### 4) Acceso a la aplicación
- **Aplicación web**: http://127.0.0.1:8000
- **Panel admin**: http://127.0.0.1:8000/admin (admin/admin1234)
- **API Docs**: http://127.0.0.1:8000/api/docs/
- **Gestión blackouts**: http://127.0.0.1:8000/bloqueos/ (requiere login admin)

### 5) Desarrollo
- **Live reload**: El volumen `.:/app` permite editar código y ver cambios inmediatamente
- **Reconstruir**: Si cambias `requirements.txt`: `docker compose build web`
- **Logs**: `docker compose logs -f web` para ver logs en tiempo real
- **Base de datos**: MySQL expuesto en puerto `3308` para conexiones externas

## Usuarios de Prueba
Creados automáticamente con `create_sample_users`:
- **Admin**: `admin` / `admin1234`
