"""
test_api_accesos.py
Pruebas del endpoint /api/accesos
Cubre el flujo más crítico: validación biométrica desde terminal.
"""
import pytest
from unittest.mock import AsyncMock, patch
from domain.entities.acceso_log import ResultadoAcceso


# ── POST /api/accesos/validar ──────────────────────────────────────────────────
class TestValidarAcceso:
    """
    Este endpoint es llamado por la terminal facial.
    No requiere JWT — la terminal es un dispositivo de confianza de red interna.
    """

    def test_acceso_exitoso_retorna_200(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=True,
            resultado=ResultadoAcceso.EXITOSO,
            casillero_numero="A2-001",
            mensaje="Bienvenido Juan",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            response = client.post("/api/accesos/validar", json=solicitud_acceso_payload)
        assert response.status_code == 200

    def test_acceso_exitoso_retorna_permitido_true(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=True,
            resultado=ResultadoAcceso.EXITOSO,
            casillero_numero="A2-001",
            mensaje="Bienvenido Juan",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            data = client.post("/api/accesos/validar", json=solicitud_acceso_payload).json()
        assert data["permitido"] is True

    def test_acceso_exitoso_retorna_numero_casillero(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=True,
            resultado=ResultadoAcceso.EXITOSO,
            casillero_numero="A2-001",
            mensaje="Bienvenido",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            data = client.post("/api/accesos/validar", json=solicitud_acceso_payload).json()
        assert data["casillero_numero"] == "A2-001"

    def test_acceso_biometria_fallida_retorna_200_con_denegado(self, client, solicitud_acceso_payload):
        """El endpoint siempre retorna 200; la denegación va en el campo 'permitido'."""
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=False,
            resultado=ResultadoAcceso.DENEGADO_BIOMETRIA,
            mensaje="Rostro no reconocido",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            response = client.post("/api/accesos/validar", json=solicitud_acceso_payload)
        assert response.status_code == 200

    def test_acceso_denegado_retorna_permitido_false(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=False,
            resultado=ResultadoAcceso.DENEGADO_BIOMETRIA,
            mensaje="Rostro no reconocido",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            data = client.post("/api/accesos/validar", json=solicitud_acceso_payload).json()
        assert data["permitido"] is False

    def test_acceso_usuario_inactivo_retorna_denegado(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=False,
            resultado=ResultadoAcceso.DENEGADO_USUARIO_INACTIVO,
            mensaje="Acceso denegado: usuario inactivo",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            data = client.post("/api/accesos/validar", json=solicitud_acceso_payload).json()
        assert data["resultado"] == ResultadoAcceso.DENEGADO_USUARIO_INACTIVO

    def test_acceso_fuera_horario_retorna_denegado(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=False,
            resultado=ResultadoAcceso.DENEGADO_FUERA_HORARIO,
            mensaje="Acceso denegado: fuera de horario",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            data = client.post("/api/accesos/validar", json=solicitud_acceso_payload).json()
        assert data["resultado"] == ResultadoAcceso.DENEGADO_FUERA_HORARIO

    def test_acceso_sin_imagen_retorna_422(self, client):
        response = client.post("/api/accesos/validar", json={"terminal_id": "term-p1"})
        assert response.status_code == 422

    def test_acceso_sin_terminal_retorna_422(self, client):
        response = client.post("/api/accesos/validar", json={"imagen_base64": "base64data=="})
        assert response.status_code == 422

    def test_acceso_body_vacio_retorna_422(self, client):
        response = client.post("/api/accesos/validar", json={})
        assert response.status_code == 422

    def test_acceso_retorna_todos_los_campos(self, client, solicitud_acceso_payload):
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=True,
            resultado=ResultadoAcceso.EXITOSO,
            casillero_numero="B1-007",
            mensaje="Bienvenido",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            data = client.post("/api/accesos/validar", json=solicitud_acceso_payload).json()
        for campo in ["permitido", "resultado", "casillero_numero", "mensaje"]:
            assert campo in data, f"Campo '{campo}' faltante en respuesta"

    def test_acceso_no_requiere_jwt(self, client, solicitud_acceso_payload):
        """La terminal facial no usa JWT, va por red interna."""
        from application.accesos.validar_acceso import ResultadoAccesoDTO
        resultado_mock = ResultadoAccesoDTO(
            permitido=False,
            resultado=ResultadoAcceso.DENEGADO_BIOMETRIA,
            mensaje="Denegado",
        )
        with patch("application.accesos.validar_acceso.ValidarAcceso.ejecutar",
                   new=AsyncMock(return_value=resultado_mock)):
            response = client.post("/api/accesos/validar", json=solicitud_acceso_payload)
        assert response.status_code != 401


# ── GET /api/accesos/historial/{usuario_id} ────────────────────────────────────
class TestHistorialAccesos:

    def test_historial_retorna_200(self, client):
        from domain.entities.acceso_log import AccesoLog
        from datetime import datetime
        log_mock = AccesoLog(
            id=1, usuario_id=1, casillero_id=1,
            terminal_id="term-p1-entrada",
            resultado=ResultadoAcceso.EXITOSO,
            confianza_biometrica=0.95,
            timestamp=datetime.utcnow(),
        )
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_usuario",
                   new=AsyncMock(return_value=[log_mock])):
            response = client.get("/api/accesos/historial/1")
        assert response.status_code == 200

    def test_historial_retorna_lista(self, client):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_usuario",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/accesos/historial/1").json()
        assert isinstance(data, list)

    def test_historial_items_tienen_campos_requeridos(self, client):
        from domain.entities.acceso_log import AccesoLog
        from datetime import datetime
        log_mock = AccesoLog(
            id=1, usuario_id=1, casillero_id=1,
            terminal_id="term-p1-entrada",
            resultado=ResultadoAcceso.EXITOSO,
            confianza_biometrica=0.95,
            timestamp=datetime.utcnow(),
        )
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_usuario",
                   new=AsyncMock(return_value=[log_mock])):
            data = client.get("/api/accesos/historial/1").json()
        if data:
            item = data[0]
            for campo in ["id", "resultado", "timestamp", "casillero_id", "confianza"]:
                assert campo in item, f"Campo '{campo}' faltante"

    def test_historial_usuario_inexistente_retorna_lista_vacia(self, client):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_usuario",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/accesos/historial/9999").json()
        assert data == []
