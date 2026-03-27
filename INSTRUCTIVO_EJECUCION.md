# Instructivo de Ejecución — Sistema de Casilleros Automatizados
**Versión:** 1.0
**Fecha:** Marzo 2026
**Dirigido a:** Administradores del sistema

---

## Requisitos previos

Antes de ejecutar el sistema, el equipo debe tener instalado:

| Requisito | Descripción |
|-----------|-------------|
| **Docker Desktop** | Motor que ejecuta todos los servicios del sistema |
| **Windows 10/11** (64 bits) | Sistema operativo compatible |
| **8 GB RAM mínimo** | Recursos recomendados para funcionamiento estable |
| **Conexión a Internet** | Solo la primera vez, para descargar componentes |

---

## Paso 1 — Instalar Docker Desktop

> Si Docker Desktop ya está instalado, omita este paso y continúe en el Paso 2.

1. Abrir el navegador e ir a: **https://www.docker.com/products/docker-desktop**
2. Hacer clic en **"Download for Windows"**
3. Ejecutar el instalador descargado (`Docker Desktop Installer.exe`)
4. Seguir el asistente de instalación con las opciones predeterminadas
5. Al finalizar, **reiniciar el equipo**
6. Después del reinicio, Docker Desktop se abrirá automáticamente

---

## Paso 2 — Verificar que Docker está corriendo

Antes de ejecutar el sistema, confirme que Docker Desktop esté activo:

1. Buscar el ícono de la **ballena** 🐳 en la barra de tareas (esquina inferior derecha)
2. El ícono debe mostrar el mensaje **"Docker Desktop is running"** al posicionarse sobre él

> ⚠️ **Si el ícono no aparece:** Buscar "Docker Desktop" en el menú de inicio y abrirlo. Esperar 1-2 minutos hasta que cargue completamente.

---

## Paso 3 — Ejecutar el sistema

1. Navegar a la carpeta del proyecto:
   ```
   C:\proyectos\casilleros\dist\
   ```
2. Hacer **doble clic** en el archivo:
   ```
   Casilleros-Launcher.exe
   ```
3. Se abrirá la siguiente ventana:

   ```
   ┌─────────────────────────────────────────┐
   │  🔒  CASILLEROS AUTOMATIZADOS           │
   │      Sistema de gestión v1.0            │
   ├─────────────────────────────────────────┤
   │  Estado Docker:  ✔ Corriendo            │
   │  Servicios:      —                      │
   │                                         │
   │  [ Log del sistema ]                    │
   │                                         │
   │  ▶ Levantar  ■ Detener  🌐 Abrir       │
   └─────────────────────────────────────────┘
   ```

4. Hacer clic en el botón **"▶ Levantar sistema"**
5. Esperar mientras se inician los servicios (puede tomar entre **1 y 3 minutos** la primera vez)
6. Cuando los servicios estén listos, el navegador **se abrirá automáticamente** con el sistema

---

## Paso 4 — Acceder al sistema

Una vez que el navegador se abra automáticamente, se mostrará la pantalla de inicio de sesión.

**URL de acceso:**
```
http://localhost
```

**Credenciales de acceso:**

| Usuario | Correo electrónico | Contraseña | Rol |
|---------|-------------------|------------|-----|
| Admin Sistema | `admin@empresa.com` | `Admin1234` | Superadmin |
| Wilmer Aucancela | `waucancela@telconet.ec` | `Admin1234` | Superadmin |
| Carlos Velastegui | `clvelastegui@telconet.ec` | _(contactar a soporte)_ | Admin |

**Niveles de acceso:**

| Rol | Permisos |
|-----|----------|
| **Superadmin** | Acceso total: gestión de usuarios, casilleros, administradores y reportes |
| **Admin** | Gestión de usuarios y casilleros, sin acceso a configuración de administradores |
| **Viewer** | Solo lectura: puede ver reportes pero no realizar modificaciones |

> 🔒 Por seguridad, se recomienda cambiar la contraseña en el primer inicio de sesión.

---

## Paso 5 — Acceso a la base de datos

La base de datos puede consultarse con cualquier cliente PostgreSQL como **DBeaver** (gratuito) o **pgAdmin**.

> ⚠️ El sistema debe estar **levantado** para poder conectarse a la base de datos.

**Datos de conexión:**

| Parámetro | Valor |
|-----------|-------|
| **Host** | `localhost` |
| **Puerto** | `5432` |
| **Base de datos** | `casilleros` |
| **Usuario** | `casilleros_user` |
| **Contraseña** | `MiPassword2026!` |

---

### Conectarse con DBeaver (recomendado)

1. Descargar e instalar DBeaver desde: **https://dbeaver.io/download/**
2. Abrir DBeaver y hacer clic en **"Nueva conexión"** (ícono de enchufe)
3. Seleccionar **PostgreSQL** y hacer clic en **Siguiente**
4. Completar los datos de conexión de la tabla anterior
5. Hacer clic en **"Test Connection"** — debe mostrar **"Connected"**
6. Hacer clic en **Finalizar**

---

### Tablas principales del sistema

| Tabla | Descripción |
|-------|-------------|
| `administradores` | Usuarios con acceso al panel de gestión |
| `usuarios` | Empleados que usan los casilleros |
| `casilleros` | Registro de cada casillero físico |
| `accesos_log` | Historial completo de accesos al sistema |
| `controladores` | Dispositivos físicos que manejan las cerraduras |
| `terminales` | Dispositivos de reconocimiento facial |
| `alertas` | Eventos que requieren atención del administrador |
| `horarios_acceso` | Horarios permitidos por departamento |

---

### Vistas útiles para consultas rápidas

| Vista | Descripción |
|-------|-------------|
| `v_casilleros_con_usuario` | Estado de cada casillero con datos del usuario asignado |
| `v_ocupacion_por_piso` | Resumen de ocupación por piso |
| `v_accesos_recientes` | Últimos accesos con nombre de usuario |

> 🔒 Se recomienda acceder a la base de datos **solo en modo lectura** para consultas y reportes. Cualquier modificación directa debe ser coordinada con el equipo de desarrollo.

---

## Paso 6 — Detener el sistema

Cuando ya no necesite usar el sistema:

1. Cerrar la conexión de DBeaver si estaba conectado
2. Volver al **Casilleros-Launcher**
3. Hacer clic en el botón **"■ Detener"**
4. Confirmar la acción en el mensaje que aparece
5. Esperar a que los servicios se apaguen correctamente

> ✅ También puede cerrar la ventana del Launcher sin detener los servicios. En ese caso, el sistema continuará corriendo en segundo plano y podrá acceder desde el navegador en `http://localhost`.

---

## Solución de problemas frecuentes

### El Launcher muestra "Docker no disponible"
**Causa:** Docker Desktop no está iniciado.
**Solución:**
1. Buscar "Docker Desktop" en el menú de inicio
2. Abrirlo y esperar a que aparezca el ícono de la ballena en la barra de tareas
3. Volver a hacer clic en "▶ Levantar sistema"

---

### El navegador no abre automáticamente
**Solución:** Abrir el navegador manualmente e ir a:
```
http://localhost
```

---

### El sistema tarda más de 5 minutos en levantar
**Causa:** Puede ser la primera vez que se ejecuta y está descargando componentes.
**Solución:** Esperar con paciencia. Una vez descargados, las siguientes ejecuciones tardarán menos de 30 segundos.

---

### La pantalla de login muestra error 400 o 401
**Causa:** Credenciales incorrectas.
**Solución:** Verificar que el correo y contraseña estén escritos correctamente (respeta mayúsculas y minúsculas).

---

### El puerto 80 está en uso
**Causa:** Otro servicio del equipo está usando el puerto 80 (IIS, otro servidor web).
**Solución:** Contactar al equipo de soporte técnico.

---

## Servicios que componen el sistema

| Servicio | Descripción | Puerto |
|----------|-------------|--------|
| **Frontend (Nginx)** | Interfaz web del sistema | 80 |
| **Backend (FastAPI)** | API y lógica del negocio | 8000 |
| **Base de datos (PostgreSQL)** | Almacenamiento de datos | 5432 |
| **Mensajería (Mosquitto MQTT)** | Comunicación con hardware | 1883 |

---

## Contacto de soporte

Para problemas técnicos, contactar al equipo de desarrollo:

| | |
|-|-|
| **Responsable** | Wilmer Aucancela |
| **Correo** | waucancela@telconet.ec |

---

*Sistema de Casilleros Automatizados — Documento interno confidencial*
