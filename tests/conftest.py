"""
conftest.py
Fixtures compartidos para todas las pruebas de la capa API.
Usa TestClient de FastAPI con dependencias mockeadas (sin BD real ni hardware).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# ── Patch de infraestructura ANTES de importar la app ─────────────────────────
# Esto evita que se intente conectar a PostgreSQL, MQTT o DeepFace al iniciar los tests

@pytest.fixture(scope="session", autouse=True)
def patch_infraestructura():
    """Parchea toda la infraestructura externa para tests."""
    with patch("infrastructure.database.conexion.create_async_engine"), \
         patch("infrastructure.database.conexion.AsyncSessionLocal"), \
         patch("infrastructure.hardware.controlador_mqtt.controlador_mqtt"), \
         patch("infrastructure.biometria.motor_facial.MotorFacial"), \
         patch("infrastructure.biometria.encriptacion_vectores.EncriptacionVectores"):
        yield

# ── App y cliente ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def app():
    from main import app as fastapi_app
    return fastapi_app

@pytest.fixture(scope="session")
def client(app):
    with TestClient(app) as c:
        yield c

# ── Token de autenticación ─────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def token_admin():
    """JWT válido para un administrador."""
    from api.middlewares.auth_middleware import crear_token
    return crear_token(usuario_id=1, rol="admin")

@pytest.fixture(scope="session")
def token_viewer():
    """JWT válido para un usuario con rol viewer (sin permisos admin)."""
    from api.middlewares.auth_middleware import crear_token
    return crear_token(usuario_id=99, rol="viewer")

@pytest.fixture(scope="session")
def headers_admin(token_admin):
    return {"Authorization": f"Bearer {token_admin}"}

@pytest.fixture(scope="session")
def headers_viewer(token_viewer):
    return {"Authorization": f"Bearer {token_viewer}"}

# ── Datos de prueba reutilizables ──────────────────────────────────────────────
@pytest.fixture
def usuario_payload():
    return {
        "nombre":        "Juan",
        "apellido":      "Pérez",
        "email":         "juan.perez@empresa.com",
        "departamento":  "Tecnología",
        "piso_preferido": 2,
    }

@pytest.fixture
def usuario_payload_invalido():
    return {
        "nombre": "",          # Nombre vacío — inválido
        "apellido": "Pérez",
        "email": "no-es-un-email",
        "departamento": "",
    }

@pytest.fixture
def solicitud_acceso_payload():
    return {
        "imagen_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAgAAZABkAAD",
        "terminal_id":   "term-p1-entrada",
    }

@pytest.fixture
def mock_db():
    """Sesión de BD mockeada para inyectar en dependencias."""
    db = AsyncMock()
    db.commit  = AsyncMock()
    db.rollback= AsyncMock()
    db.close   = AsyncMock()
    db.flush   = AsyncMock()
    db.execute = AsyncMock()
    db.add     = MagicMock()
    return db

@pytest.fixture
def mock_usuario():
    """Entidad Usuario mockeada."""
    from domain.entities.usuario import Usuario, EstadoUsuario
    return Usuario(
        id=1,
        nombre="Juan",
        apellido="Pérez",
        email="juan.perez@empresa.com",
        departamento="Tecnología",
        piso_preferido=2,
        estado=EstadoUsuario.ACTIVO,
    )

@pytest.fixture
def mock_casillero():
    """Entidad Casillero mockeada."""
    from domain.entities.casillero import Casillero, EstadoCasillero
    return Casillero(
        id=1,
        numero="A2-001",
        piso=2,
        zona="A",
        controlador_id="ctrl-p2-a",
        puerto_controlador=1,
        estado=EstadoCasillero.LIBRE,
    )
