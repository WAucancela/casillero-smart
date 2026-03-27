"""
test_api_usuarios.py
Pruebas completas del endpoint /api/usuarios
Cubre: creación, baja, registro biométrico, validación de datos.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from domain.entities.usuario import Usuario, EstadoUsuario


# ── Helpers ────────────────────────────────────────────────────────────────────
def mock_usuario_guardado(payload: dict) -> Usuario:
    return Usuario(
        id=10,
        nombre=payload["nombre"],
        apellido=payload["apellido"],
        email=payload["email"],
        departamento=payload["departamento"],
        piso_preferido=payload.get("piso_preferido"),
        estado=EstadoUsuario.PENDIENTE_BIOMETRIA,
    )


# ── POST /api/usuarios/ ────────────────────────────────────────────────────────
class TestCrearUsuario:

    def test_crear_usuario_valido_retorna_200(self, client, headers_admin, usuario_payload):
        usuario_mock = mock_usuario_guardado(usuario_payload)
        with patch("application.usuarios.crear_usuario.CrearUsuario.ejecutar",
                   new=AsyncMock(return_value=usuario_mock)):
            response = client.post("/api/usuarios/", json=usuario_payload, headers=headers_admin)
        assert response.status_code == 200

    def test_crear_usuario_retorna_id_y_email(self, client, headers_admin, usuario_payload):
        usuario_mock = mock_usuario_guardado(usuario_payload)
        with patch("application.usuarios.crear_usuario.CrearUsuario.ejecutar",
                   new=AsyncMock(return_value=usuario_mock)):
            data = client.post("/api/usuarios/", json=usuario_payload, headers=headers_admin).json()
        assert "id" in data
        assert data["email"] == usuario_payload["email"]

    def test_crear_usuario_retorna_estado_pendiente(self, client, headers_admin, usuario_payload):
        usuario_mock = mock_usuario_guardado(usuario_payload)
        with patch("application.usuarios.crear_usuario.CrearUsuario.ejecutar",
                   new=AsyncMock(return_value=usuario_mock)):
            data = client.post("/api/usuarios/", json=usuario_payload, headers=headers_admin).json()
        assert data["estado"] == EstadoUsuario.PENDIENTE_BIOMETRIA

    def test_crear_usuario_email_invalido_retorna_422(self, client, headers_admin):
        payload = {
            "nombre": "Juan", "apellido": "Pérez",
            "email": "no-es-email",           # ← inválido
            "departamento": "Tecnología",
        }
        response = client.post("/api/usuarios/", json=payload, headers=headers_admin)
        assert response.status_code == 422

    def test_crear_usuario_sin_nombre_retorna_422(self, client, headers_admin):
        payload = {"apellido": "Pérez", "email": "j@empresa.com", "departamento": "TI"}
        response = client.post("/api/usuarios/", json=payload, headers=headers_admin)
        assert response.status_code == 422

    def test_crear_usuario_email_duplicado_retorna_400(self, client, headers_admin, usuario_payload):
        with patch("application.usuarios.crear_usuario.CrearUsuario.ejecutar",
                   new=AsyncMock(side_effect=ValueError("Ya existe un usuario con ese email"))):
            response = client.post("/api/usuarios/", json=usuario_payload, headers=headers_admin)
        assert response.status_code == 400

    def test_crear_usuario_sin_auth_retorna_401(self, client, usuario_payload):
        response = client.post("/api/usuarios/", json=usuario_payload)
        assert response.status_code == 401

    def test_crear_usuario_sin_departamento_retorna_422(self, client, headers_admin):
        payload = {"nombre": "Juan", "apellido": "Pérez", "email": "j@empresa.com"}
        response = client.post("/api/usuarios/", json=payload, headers=headers_admin)
        assert response.status_code == 422


# ── DELETE /api/usuarios/{id} ──────────────────────────────────────────────────
class TestDarBajaUsuario:

    def test_dar_baja_exitoso_retorna_200(self, client, headers_admin):
        with patch("application.usuarios.dar_baja_usuario.DarBajaUsuario.ejecutar",
                   new=AsyncMock(return_value=True)):
            response = client.delete("/api/usuarios/1", headers=headers_admin)
        assert response.status_code == 200

    def test_dar_baja_retorna_mensaje_confirmacion(self, client, headers_admin):
        with patch("application.usuarios.dar_baja_usuario.DarBajaUsuario.ejecutar",
                   new=AsyncMock(return_value=True)):
            data = client.delete("/api/usuarios/1", headers=headers_admin).json()
        assert "mensaje" in data
        assert "1" in data["mensaje"]

    def test_dar_baja_usuario_inexistente_retorna_400(self, client, headers_admin):
        with patch("application.usuarios.dar_baja_usuario.DarBajaUsuario.ejecutar",
                   new=AsyncMock(side_effect=ValueError("Usuario no encontrado: 999"))):
            response = client.delete("/api/usuarios/999", headers=headers_admin)
        assert response.status_code == 400

    def test_dar_baja_sin_auth_retorna_401(self, client):
        response = client.delete("/api/usuarios/1")
        assert response.status_code == 401


# ── POST /api/usuarios/{id}/biometria ─────────────────────────────────────────
class TestRegistrarBiometria:

    def test_registrar_biometria_exitoso_retorna_200(self, client, headers_admin):
        payload = {"imagen_base64": "base64encodedimagedata=="}
        with patch("application.usuarios.registrar_biometria.RegistrarBiometria.ejecutar",
                   new=AsyncMock(return_value=True)):
            response = client.post("/api/usuarios/1/biometria", json=payload, headers=headers_admin)
        assert response.status_code == 200

    def test_registrar_biometria_retorna_mensaje(self, client, headers_admin):
        payload = {"imagen_base64": "base64encodedimagedata=="}
        with patch("application.usuarios.registrar_biometria.RegistrarBiometria.ejecutar",
                   new=AsyncMock(return_value=True)):
            data = client.post("/api/usuarios/1/biometria", json=payload, headers=headers_admin).json()
        assert "mensaje" in data

    def test_registrar_biometria_imagen_invalida_retorna_400(self, client, headers_admin):
        payload = {"imagen_base64": "imagen_invalida"}
        with patch("application.usuarios.registrar_biometria.RegistrarBiometria.ejecutar",
                   new=AsyncMock(side_effect=ValueError("No se pudo detectar un rostro válido"))):
            response = client.post("/api/usuarios/1/biometria", json=payload, headers=headers_admin)
        assert response.status_code == 400

    def test_registrar_biometria_usuario_inexistente_retorna_400(self, client, headers_admin):
        payload = {"imagen_base64": "base64data=="}
        with patch("application.usuarios.registrar_biometria.RegistrarBiometria.ejecutar",
                   new=AsyncMock(side_effect=ValueError("Usuario no encontrado: 999"))):
            response = client.post("/api/usuarios/999/biometria", json=payload, headers=headers_admin)
        assert response.status_code == 400

    def test_registrar_biometria_sin_imagen_retorna_422(self, client, headers_admin):
        response = client.post("/api/usuarios/1/biometria", json={}, headers=headers_admin)
        assert response.status_code == 422


# ── GET /api/usuarios/ ─────────────────────────────────────────────────────────
class TestListarUsuarios:

    def test_listar_retorna_200(self, client, headers_admin, mock_usuario):
        with patch("infrastructure.database.usuario_repo.UsuarioRepository.listar_todos",
                   new=AsyncMock(return_value=[mock_usuario])):
            response = client.get("/api/usuarios/", headers=headers_admin)
        assert response.status_code == 200

    def test_listar_retorna_lista(self, client, headers_admin, mock_usuario):
        with patch("infrastructure.database.usuario_repo.UsuarioRepository.listar_todos",
                   new=AsyncMock(return_value=[mock_usuario])):
            data = client.get("/api/usuarios/", headers=headers_admin).json()
        assert isinstance(data, list)

    def test_listar_items_tienen_campos_requeridos(self, client, headers_admin, mock_usuario):
        with patch("infrastructure.database.usuario_repo.UsuarioRepository.listar_todos",
                   new=AsyncMock(return_value=[mock_usuario])):
            data = client.get("/api/usuarios/", headers=headers_admin).json()
        if data:
            item = data[0]
            for campo in ["id", "nombre_completo", "email", "departamento", "estado"]:
                assert campo in item, f"Campo '{campo}' faltante en respuesta"

    def test_listar_sin_auth_retorna_401(self, client):
        response = client.get("/api/usuarios/")
        assert response.status_code == 401
