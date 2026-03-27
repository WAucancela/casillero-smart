# Base de Datos — Sistema de Casilleros Automatizados

## Estructura

```
database/
├── schema.sql                          ← Esquema completo (referencia)
├── alembic.ini                         ← Configuración de migraciones
├── migrations/
│   ├── env.py                          ← Entorno async de Alembic
│   └── versions/
│       ├── 001_tablas_base.py          ← Tablas, índices
│       └── 002_vistas_seeds.py         ← Vistas SQL + datos iniciales
└── seeds/
    └── seed_data.py                    ← Datos de prueba
```

## Tablas principales

| Tabla | Descripción |
|---|---|
| `administradores` | Usuarios del panel de gestión |
| `usuarios` | Empleados que usan los casilleros |
| `biometria` | Vectores faciales encriptados (AES-256) |
| `controladores` | Dispositivos físicos de cerraduras |
| `casilleros` | Cada casillero físico del sistema |
| `terminales` | Cámaras de reconocimiento facial |
| `accesos_log` | Historial de cada intento de acceso |
| `horarios_acceso` | Ventanas de tiempo permitidas |
| `alertas` | Eventos que requieren atención |

## Vistas disponibles

| Vista | Descripción |
|---|---|
| `v_casilleros_con_usuario` | Estado de casilleros con datos del ocupante |
| `v_ocupacion_por_piso` | Resumen de ocupación agrupado por piso |
| `v_accesos_recientes` | Últimos accesos con nombres de usuario |

---

## Instalación paso a paso

### 1. Crear la base de datos en PostgreSQL

```sql
CREATE DATABASE casilleros_db;
CREATE USER casilleros_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE casilleros_db TO casilleros_user;
```

### 2. Configurar la URL en alembic.ini

```ini
sqlalchemy.url = postgresql+asyncpg://casilleros_user:tu_password@localhost:5432/casilleros_db
```

### 3. Instalar dependencias

```bash
pip install alembic asyncpg sqlalchemy passlib bcrypt
```

### 4. Ejecutar migraciones

```bash
cd database/

# Ver estado actual
alembic current

# Aplicar todas las migraciones
alembic upgrade head

# Ver historial
alembic history
```

### 5. Poblar datos de prueba (solo desarrollo)

```bash
python seeds/seed_data.py
```

---

## Comandos útiles de Alembic

```bash
# Crear nueva migración vacía
alembic revision -m "descripcion_del_cambio"

# Crear migración detectando cambios automáticamente
alembic revision --autogenerate -m "descripcion"

# Aplicar hasta una versión específica
alembic upgrade 001_tablas_base

# Revertir última migración
alembic downgrade -1

# Revertir todo
alembic downgrade base
```

---

## Credenciales por defecto (cambiar antes de producción)

| Campo | Valor |
|---|---|
| Email admin | `admin@empresa.com` |
| Contraseña | `Admin123!` |

> ⚠️ **IMPORTANTE**: Cambiar la contraseña del superadmin antes de desplegar en producción.
