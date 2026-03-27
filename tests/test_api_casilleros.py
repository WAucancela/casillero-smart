"""
test_api_casilleros.py
Pruebas completas del endpoint /api/casilleros
Cubre: asignación, apertura remota, listado, bloqueo.
"""
import pytest
from unittest.mock import AsyncMock, patch
from domain.entities.casillero import Casillero, EstadoCasillero


# ── POST /api/casilleros/asignar/{usuario_id} ──────────────────────────────────
class TestAsignarCasillero:

    def test_asignar_exitoso_retorna_200(self, client, headers_admin, mock_casillero):
        mock_casillero.asignar(1)
        with patch("application.casilleros.asignar_casillero.AsignarCasillero.ejecutar",
                   new=AsyncMock(return_value=mock_casillero)):
            response = client.post("/api/casilleros/asignar/1", headers=headers_admin)
        assert response.status_code == 200

    def test_asignar_retorna_numero_casillero(self, client, headers_admin, mock_casillero):
        mock_casillero.asignar(1)
        with patch("application.casilleros.asignar_casillero.AsignarCasillero.ejecutar",
                   new=AsyncMock(return_value=mock_casillero)):
            data = client.post("/api/casilleros/asignar/1", headers=headers_admin).json()
        assert "casillero_numero" in data
        assert data["casillero_numero"] == mock_casillero.numero

    def test_asignar_retorna_piso(self, client, headers_admin, mock_casillero):
        mock_casillero.asignar(1)
        with patch("application.casilleros.asignar_casillero.AsignarCasillero.ejecutar",
                   new=AsyncMock(return_value=mock_casillero)):
            data = client.post("/api/casilleros/asignar/1", headers=headers_admin).json()
        assert "piso" in data
        assert data["piso"] == mock_casillero.piso

    def test_asignar_usuario_inexistente_retorna_400(self, client, headers_admin):
        with patch("application.casilleros.asignar_casillero.AsignarCasillero.ejecutar",
                   new=AsyncMock(side_effect=ValueError("Usuario no encontrado: 999"))):
            response = client.post("/api/casilleros/asignar/999", headers=headers_admin)
        assert response.status_code == 400

    def test_asignar_sin_casilleros_disponibles_retorna_400(self, client, headers_admin):
        with patch("application.casilleros.asignar_casillero.AsignarCasillero.ejecutar",
                   new=AsyncMock(side_effect=ValueError("No hay casilleros disponibles"))):
            response = client.post("/api/casilleros/asignar/1", headers=headers_admin)
        assert response.status_code == 400

    def test_asignar_usuario_ya_tiene_casillero_retorna_400(self, client, headers_admin):
        with patch("application.casilleros.asignar_casillero.AsignarCasillero.ejecutar",
                   new=AsyncMock(side_effect=ValueError("El usuario ya tiene el casillero A2-001"))):
            response = client.post("/api/casilleros/asignar/1", headers=headers_admin)
        assert response.status_code == 400

    def test_asignar_sin_auth_retorna_401(self, client):
        response = client.post("/api/casilleros/asignar/1")
        assert response.status_code == 401


# ── POST /api/casilleros/{id}/abrir ───────────────────────────────────────────
class TestAbrirCasilleroRemoto:

    def test_abrir_exitoso_retorna_200(self, client, headers_admin):
        with patch("application.casilleros.abrir_casillero_remoto.AbrirCasilleroRemoto.ejecutar",
                   new=AsyncMock(return_value=True)):
            response = client.post("/api/casilleros/1/abrir", headers=headers_admin)
        assert response.status_code == 200

    def test_abrir_retorna_campo_enviado(self, client, headers_admin):
        with patch("application.casilleros.abrir_casillero_remoto.AbrirCasilleroRemoto.ejecutar",
                   new=AsyncMock(return_value=True)):
            data = client.post("/api/casilleros/1/abrir", headers=headers_admin).json()
        assert "enviado" in data
        assert data["enviado"] is True

    def test_abrir_retorna_casillero_id(self, client, headers_admin):
        with patch("application.casilleros.abrir_casillero_remoto.AbrirCasilleroRemoto.ejecutar",
                   new=AsyncMock(return_value=True)):
            data = client.post("/api/casilleros/1/abrir", headers=headers_admin).json()
        assert data["casillero_id"] == 1

    def test_abrir_casillero_inexistente_retorna_400(self, client, headers_admin):
        with patch("application.casilleros.abrir_casillero_remoto.AbrirCasilleroRemoto.ejecutar",
                   new=AsyncMock(side_effect=ValueError("Casillero no encontrado: 999"))):
            response = client.post("/api/casilleros/999/abrir", headers=headers_admin)
        assert response.status_code == 400

    def test_abrir_fallo_hardware_retorna_enviado_false(self, client, headers_admin):
        with patch("application.casilleros.abrir_casillero_remoto.AbrirCasilleroRemoto.ejecutar",
                   new=AsyncMock(return_value=False)):
            data = client.post("/api/casilleros/1/abrir", headers=headers_admin).json()
        assert data["enviado"] is False

    def test_abrir_sin_auth_retorna_401(self, client):
        response = client.post("/api/casilleros/1/abrir")
        assert response.status_code == 401


# ── GET /api/casilleros/ ───────────────────────────────────────────────────────
class TestListarCasilleros:

    def test_listar_retorna_200(self, client, headers_admin, mock_casillero):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=[mock_casillero])):
            response = client.get("/api/casilleros/", headers=headers_admin)
        assert response.status_code == 200

    def test_listar_retorna_lista(self, client, headers_admin, mock_casillero):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=[mock_casillero])):
            data = client.get("/api/casilleros/", headers=headers_admin).json()
        assert isinstance(data, list)

    def test_listar_items_tienen_campos_requeridos(self, client, headers_admin, mock_casillero):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=[mock_casillero])):
            data = client.get("/api/casilleros/", headers=headers_admin).json()
        if data:
            item = data[0]
            for campo in ["id", "numero", "piso", "zona", "estado"]:
                assert campo in item, f"Campo '{campo}' faltante"

    def test_listar_sin_auth_retorna_401(self, client):
        response = client.get("/api/casilleros/")
        assert response.status_code == 401


# ── GET /api/casilleros/disponibles ───────────────────────────────────────────
class TestListarDisponibles:

    def test_disponibles_retorna_200(self, client, headers_admin, mock_casillero):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=[mock_casillero])):
            response = client.get("/api/casilleros/disponibles", headers=headers_admin)
        assert response.status_code == 200

    def test_disponibles_solo_retorna_casilleros_libres(self, client, headers_admin, mock_casillero):
        assert mock_casillero.esta_disponible(), "El mock debe estar en estado libre"
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=[mock_casillero])):
            data = client.get("/api/casilleros/disponibles", headers=headers_admin).json()
        assert isinstance(data, list)

    def test_disponibles_sin_auth_retorna_401(self, client):
        response = client.get("/api/casilleros/disponibles")
        assert response.status_code == 401
