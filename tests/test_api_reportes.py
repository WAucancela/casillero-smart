"""
test_api_reportes.py
Pruebas del endpoint /api/reportes
Cubre: reporte de accesos por fechas y reporte de ocupación.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from domain.entities.acceso_log import AccesoLog, ResultadoAcceso
from domain.entities.casillero import Casillero, EstadoCasillero


# ── Helpers ────────────────────────────────────────────────────────────────────
def crear_log(resultado=ResultadoAcceso.EXITOSO, offset_horas=0):
    return AccesoLog(
        id=1,
        usuario_id=1,
        casillero_id=1,
        terminal_id="term-p1-entrada",
        resultado=resultado,
        confianza_biometrica=0.92 if resultado == ResultadoAcceso.EXITOSO else 0.45,
        timestamp=datetime.utcnow() - timedelta(hours=offset_horas),
    )

def crear_casillero(estado=EstadoCasillero.LIBRE, piso=1):
    return Casillero(
        id=1, numero="A1-001", piso=piso, zona="A",
        controlador_id="ctrl-p1-a", puerto_controlador=1, estado=estado,
    )


# ── GET /api/reportes/accesos ──────────────────────────────────────────────────
class TestReporteAccesos:

    def test_reporte_retorna_200(self, client, headers_admin):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=[])):
            response = client.get("/api/reportes/accesos", headers=headers_admin)
        assert response.status_code == 200

    def test_reporte_retorna_campo_periodo(self, client, headers_admin):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert "periodo" in data

    def test_reporte_retorna_campo_resumen(self, client, headers_admin):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert "resumen" in data

    def test_reporte_retorna_campo_detalle(self, client, headers_admin):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert "detalle" in data
        assert isinstance(data["detalle"], list)

    def test_reporte_calcula_total_correctamente(self, client, headers_admin):
        logs = [crear_log(ResultadoAcceso.EXITOSO), crear_log(ResultadoAcceso.DENEGADO_BIOMETRIA)]
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=logs)):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert data["resumen"]["total_intentos"] == 2

    def test_reporte_calcula_exitosos_correctamente(self, client, headers_admin):
        logs = [
            crear_log(ResultadoAcceso.EXITOSO),
            crear_log(ResultadoAcceso.EXITOSO),
            crear_log(ResultadoAcceso.DENEGADO_BIOMETRIA),
        ]
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=logs)):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert data["resumen"]["exitosos"] == 2

    def test_reporte_calcula_denegados_correctamente(self, client, headers_admin):
        logs = [
            crear_log(ResultadoAcceso.EXITOSO),
            crear_log(ResultadoAcceso.DENEGADO_BIOMETRIA),
            crear_log(ResultadoAcceso.DENEGADO_FUERA_HORARIO),
        ]
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=logs)):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert data["resumen"]["denegados"] == 2

    def test_reporte_calcula_tasa_exito_correctamente(self, client, headers_admin):
        logs = [crear_log(ResultadoAcceso.EXITOSO)] * 3 + [crear_log(ResultadoAcceso.DENEGADO_BIOMETRIA)]
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=logs)):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert data["resumen"]["tasa_exito"] == 75.0

    def test_reporte_sin_logs_tasa_exito_es_cero(self, client, headers_admin):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/reportes/accesos", headers=headers_admin).json()
        assert data["resumen"]["tasa_exito"] == 0

    def test_reporte_acepta_filtro_usuario_id(self, client, headers_admin):
        with patch("infrastructure.database.acceso_repo.AccesoRepository.listar_por_rango_fechas",
                   new=AsyncMock(return_value=[])):
            response = client.get("/api/reportes/accesos?usuario_id=1", headers=headers_admin)
        assert response.status_code == 200

    def test_reporte_sin_auth_retorna_401(self, client):
        response = client.get("/api/reportes/accesos")
        assert response.status_code == 401


# ── GET /api/reportes/ocupacion ────────────────────────────────────────────────
class TestReporteOcupacion:

    def test_ocupacion_retorna_200(self, client, headers_admin):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=[])), \
             patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=[])):
            response = client.get("/api/reportes/ocupacion", headers=headers_admin)
        assert response.status_code == 200

    def test_ocupacion_retorna_campo_resumen(self, client, headers_admin):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=[])), \
             patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/reportes/ocupacion", headers=headers_admin).json()
        assert "resumen" in data

    def test_ocupacion_retorna_campo_por_piso(self, client, headers_admin):
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=[])), \
             patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=[])):
            data = client.get("/api/reportes/ocupacion", headers=headers_admin).json()
        assert "por_piso" in data

    def test_ocupacion_calcula_totales_correctamente(self, client, headers_admin):
        todos = [
            crear_casillero(EstadoCasillero.OCUPADO, piso=1),
            crear_casillero(EstadoCasillero.LIBRE,   piso=1),
            crear_casillero(EstadoCasillero.LIBRE,   piso=2),
        ]
        libres = [c for c in todos if c.estado == EstadoCasillero.LIBRE]
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=todos)), \
             patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=libres)):
            data = client.get("/api/reportes/ocupacion", headers=headers_admin).json()
        assert data["resumen"]["total"]   == 3
        assert data["resumen"]["libres"]  == 2
        assert data["resumen"]["ocupados"]== 1

    def test_ocupacion_porcentaje_correcto(self, client, headers_admin):
        todos  = [crear_casillero(EstadoCasillero.OCUPADO)] * 1 + [crear_casillero(EstadoCasillero.LIBRE)] * 1
        libres = [crear_casillero(EstadoCasillero.LIBRE)]
        with patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_todos",
                   new=AsyncMock(return_value=todos)), \
             patch("infrastructure.database.casillero_repo.CasilleroRepository.listar_disponibles",
                   new=AsyncMock(return_value=libres)):
            data = client.get("/api/reportes/ocupacion", headers=headers_admin).json()
        assert data["resumen"]["porcentaje_ocupacion"] == 50.0

    def test_ocupacion_sin_auth_retorna_401(self, client):
        response = client.get("/api/reportes/ocupacion")
        assert response.status_code == 401
