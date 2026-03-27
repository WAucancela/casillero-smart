# Pruebas Unitarias — Capa API

## Estructura

```
tests/
├── conftest.py              # Fixtures compartidos (cliente, tokens, mocks)
├── pytest.ini               # Configuración de pytest
├── requirements-test.txt    # Dependencias para testing
├── run_tests.sh             # Script de ejecución rápida
│
├── test_api_general.py      # Health check + autenticación JWT
├── test_api_usuarios.py     # CRUD de usuarios + biometría
├── test_api_casilleros.py   # Asignación + apertura remota
├── test_api_accesos.py      # Validación biométrica (flujo crítico)
└── test_api_reportes.py     # Reportes de accesos y ocupación
```

## Total de pruebas

| Archivo                  | Clases | Tests |
|--------------------------|--------|-------|
| test_api_general.py      | 2      | 7     |
| test_api_usuarios.py     | 4      | 17    |
| test_api_casilleros.py   | 4      | 17    |
| test_api_accesos.py      | 2      | 15    |
| test_api_reportes.py     | 2      | 14    |
| **Total**                | **14** | **70**|

## Instalación

```bash
cd tests/
pip install -r requirements-test.txt --break-system-packages
```

## Ejecución

```bash
# Todos los tests
pytest tests/ -v

# Un módulo específico
pytest tests/test_api_accesos.py -v

# Una clase específica
pytest tests/test_api_accesos.py::TestValidarAcceso -v

# Un test específico
pytest tests/test_api_accesos.py::TestValidarAcceso::test_acceso_exitoso_retorna_200 -v
```

## Estrategia

Todos los tests usan **mocks** sobre la infraestructura real:

- **Base de datos**: `AsyncMock` sobre los repositorios — no se conecta a PostgreSQL.
- **MQTT / Hardware**: parcheado en `conftest.py` — no se envían comandos reales.
- **DeepFace**: parcheado — no se procesa ninguna imagen real.
- **JWT**: se genera un token real con `crear_token()` para probar autorización.

Esto permite correr los tests sin ningún servicio externo activo.

## Casos cubiertos por módulo

### `test_api_general.py`
- `GET /health` retorna 200 y campos esperados
- Endpoints protegidos rechazan requests sin token o con token inválido
- Roles: `viewer` recibe 403 donde se requiere `admin`

### `test_api_usuarios.py`
- Crear usuario con datos válidos → 200 + estado `pendiente_biometria`
- Crear usuario con email inválido → 422
- Crear usuario con email duplicado → 400
- Dar de baja exitoso → 200 + mensaje
- Dar de baja usuario inexistente → 400
- Registrar biometría exitosa → 200
- Registrar biometría con imagen inválida → 400
- Listar usuarios → lista con campos requeridos

### `test_api_casilleros.py`
- Asignar casillero → 200 + número + piso
- Asignar sin casilleros disponibles → 400
- Asignar usuario ya con casillero → 400
- Abrir remotamente → 200 + `enviado: true`
- Abrir con fallo de hardware → `enviado: false`
- Listar todos + listar disponibles → lista con campos requeridos

### `test_api_accesos.py`
- Acceso exitoso → 200 + `permitido: true` + número de casillero
- Acceso denegado por biometría → 200 + `permitido: false`
- Acceso denegado usuario inactivo / fuera de horario
- Endpoint **no requiere JWT** (es llamado por la terminal)
- Campos faltantes en body → 422
- Historial por usuario → lista con campos requeridos

### `test_api_reportes.py`
- Reporte accesos: total, exitosos, denegados, tasa de éxito calculados correctamente
- Tasa de éxito = 0 cuando no hay logs
- Filtro por `usuario_id`
- Reporte ocupación: total, libres, ocupados, porcentaje calculados
- Ambos endpoints protegidos con JWT
