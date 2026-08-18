# Integración ZKTeco SenseFace 2A ↔ Backend FastAPI

## ¿Cómo funciona exactamente?

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO                                │
│                                                                 │
│  1. Empleado se para frente al SenseFace 2A                     │
│  2. El dispositivo reconoce el rostro INTERNAMENTE              │
│     (no necesita enviarnos la foto — ya tiene la plantilla)     │
│  3. Si reconoce → POST /iclock/cdata → nuestro backend          │
│  4. Backend valida reglas (horario, estado usuario)             │
│  5. Backend envía señal MQTT al controlador de cerradura        │
│  6. Cerradura se abre                                           │
│  7. Backend guarda el log en PostgreSQL                         │
└─────────────────────────────────────────────────────────────────┘
```

**Diferencia clave con el diseño original:**
El SenseFace 2A hace el reconocimiento facial **en el dispositivo**, no en el servidor.
Nuestro módulo DeepFace se usa para el **enrolamiento** (registrar plantillas vía panel web).
El protocolo PUSH (ADMS) solo nos notifica el resultado del reconocimiento.

---

## Paso 1 — Configurar el SenseFace 2A

### En la pantalla del dispositivo:

1. Menú → **Comm** → **Cloud Server / ADMS**
2. Configurar:

   | Campo         | Valor                              |
   |---------------|------------------------------------|
   | Server Address| `192.168.1.100` (IP de tu servidor)|
   | Server Port   | `8000`                             |
   | HTTPS         | Off (o On si tienes certificado)   |
   | Enable Push   | ✅ Activado                         |

3. Menú → **Comm** → **Ethernet**
   - Asignar IP fija al dispositivo, ej: `192.168.1.50`
   - Mismo gateway que el servidor

4. Guardar y reiniciar.

### Verificar conexión:
Después de reiniciar, el dispositivo hace un GET a:
```
GET http://192.168.1.100:8000/iclock/cdata?SN=AXHN12345678&options=
```
En los logs del backend verás:
```
INFO [ZKTeco] Handshake del dispositivo SN=AXHN12345678
```

---

## Paso 2 — Registrar el dispositivo en el backend

En `main.py`, después de crear la app FastAPI:

```python
from infrastructure.zkteco.adms_router import router as zkteco_router
from infrastructure.zkteco.dispositivo_service import registro_dispositivos

# Registrar endpoints ADMS
app.include_router(zkteco_router)

# Registrar dispositivo(s) físico(s)
# SN = número de serie impreso en el dispositivo
# IP = IP local del SenseFace 2A en tu red
registro_dispositivos.agregar(
    sn="AXHN12345678",     # ← reemplazar con el SN real
    ip="192.168.1.50",     # ← IP del SenseFace 2A
    puerto=80,
)

# Si tienes 3 dispositivos (uno por piso):
# registro_dispositivos.agregar(sn="AXHN00000001", ip="192.168.1.50")
# registro_dispositivos.agregar(sn="AXHN00000002", ip="192.168.1.51")
# registro_dispositivos.agregar(sn="AXHN00000003", ip="192.168.1.52")
```

---

## Paso 2.1 — Autorizar el dispositivo (obligatorio)

El backend **no abre ningún casillero para un SN que no haya sido autorizado
explícitamente**, aunque el handshake y el registro en `terminales_zkteco`
sean automáticos. Esto evita que cualquiera que conozca la URL del webhook
pueda simular un ZKTeco inventando un SN.

1. Hacé login en el panel con un usuario `superadmin`.
2. `GET /api/hardware/terminales` para obtener el `id` interno del terminal
   (se crea solo tras el primer handshake/evento).
3. Autorizalo:
   ```bash
   curl -X PATCH http://localhost/api/hardware/terminales/<id>/autorizar \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"autorizado": true}'
   ```

Hasta que esto se haga, cualquier evento ATTLOG de ese SN se registra en
`accesos_log` como `denegado_dispositivo_no_autorizado` y **no** abre la
cerradura, sin importar el PIN ni el horario.

Opcionalmente, si los terminales tienen IP fija, podés restringir también
por IP de origen con `ADMS_ALLOWED_IPS` en `.env` (lista separada por
comas). Vacío = sin restricción por IP.

---

## Paso 3 — Registrar usuarios en el dispositivo

Cuando creas un usuario en el panel web, también debes registrarlo en el SenseFace 2A:

```python
from infrastructure.zkteco.dispositivo_service import registro_dispositivos

dispositivo = registro_dispositivos.obtener("AXHN12345678")

# Registrar usuario (el PIN debe coincidir con usuario.id en la BD)
await dispositivo.registrar_usuario(
    pin=42,              # usuario.id
    nombre="Ana García", # se muestra en la pantalla del dispositivo
)
```

Después de esto, el empleado se para frente al dispositivo y presiona **Enroll** para registrar su rostro físicamente en el SenseFace 2A.

---

## Paso 4 — Flujo cuando alguien hace check-in

```
SenseFace 2A detecta rostro
        │
        ▼
POST /iclock/cdata
Body: "42\t2026-03-11 09:30:00\t255\t200\t0\n"
       ↑PIN  ↑timestamp          ↑255=acceso ↑200=face
        │
        ▼
adms_router.py → _procesar_linea_attlog()
        │
        ├─ Verifica que el SN esté autorizado (ver Paso 2.1) — si no, corta acá
        ├─ Busca usuario PIN=42 en PostgreSQL
        ├─ Verifica reglas (horario 06:00-22:00, estado activo)
        ├─ Si OK → MQTT → controlador → cerradura se abre
        ├─ Guarda log en accesos_log
        └─ Responde "OK: 0\n" al dispositivo
```

---

## Paso 5 — Dar de baja un usuario

```python
# Al dar de baja desde el panel web, también eliminar del dispositivo
dispositivo = registro_dispositivos.obtener("AXHN12345678")
await dispositivo.dar_baja_usuario(pin=42)
```

---

## Instalación de dependencias adicionales

```bash
pip install httpx --break-system-packages
```

---

## Estructura de archivos

```
infrastructure/
└── zkteco/
    ├── adms_router.py         ← Endpoints ADMS (/iclock/cdata, /iclock/getrequest)
    └── dispositivo_service.py ← Gestión de dispositivos (registro, comandos)
```

---

## Endpoints ADMS implementados

| Método | Ruta                  | Descripción                              |
|--------|-----------------------|------------------------------------------|
| GET    | /iclock/cdata         | Handshake inicial del dispositivo        |
| POST   | /iclock/cdata         | Receptor de eventos (acceso/asistencia)  |
| GET    | /iclock/getrequest    | Cola de comandos para el dispositivo     |
| POST   | /iclock/devicecmd     | Resultado de comandos ejecutados         |
| POST   | /iclock/cdata/photo   | Recepción de fotos de eventos            |

---

## Comandos soportados (enviados al dispositivo)

| Función                  | Cómo usarlo                                          |
|--------------------------|------------------------------------------------------|
| Registrar usuario        | `encolar_comando_usuario(sn, pin, nombre)`           |
| Eliminar usuario         | `encolar_eliminar_usuario(sn, pin)`                  |
| Abrir puerta             | `encolar_abrir_puerta(sn, segundos=5)`               |
| Sincronizar hora         | `await dispositivo.sincronizar_hora()`               |

---

## Troubleshooting

**El dispositivo no conecta:**
- Verificar que el backend corre en el puerto 8000
- Verificar que el firewall permite el puerto 8000
- Hacer ping desde el SenseFace al servidor
- Revisar que la IP del servidor en el dispositivo sea correcta

**Los eventos llegan pero no abre la cerradura:**
- Verificar que el broker MQTT está corriendo
- Verificar que el usuario tiene casillero asignado (`casillero_id`)
- Revisar los logs: `docker logs casillero-smart-backend -f`

**El PIN del usuario no coincide:**
- El PIN en el dispositivo ZKTeco debe ser igual al `id` del usuario en PostgreSQL
- Registrar usuarios con `registrar_usuario(pin=usuario.id, ...)`

**Los eventos llegan pero quedan como `denegado_dispositivo_no_autorizado`:**
- El SN todavía no fue autorizado — ver [Paso 2.1](#paso-21--autorizar-el-dispositivo-obligatorio).
