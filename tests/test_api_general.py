"""
test_api_general.py
Pruebas del endpoint de salud y autenticación JWT.
"""
import pytest


class TestHealthCheck:
    """Verifica que el servidor responde correctamente."""

    def test_health_retorna_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_health_retorna_version(self, client):
        data = client.get("/health").json()
        assert "version" in data


class TestAutenticacion:
    """Verifica que los endpoints protegidos requieren JWT válido."""

    def test_sin_token_retorna_401(self, client):
        response = client.get("/api/usuarios/")
        assert response.status_code == 401

    def test_token_invalido_retorna_401(self, client):
        response = client.get(
            "/api/usuarios/",
            headers={"Authorization": "Bearer token-falso-invalido"}
        )
        assert response.status_code == 401

    def test_token_viewer_sin_permisos_admin_retorna_403(self, client, headers_viewer):
        response = client.get("/api/usuarios/", headers=headers_viewer)
        assert response.status_code == 403

    def test_token_admin_valido_permite_acceso(self, client, headers_admin):
        response = client.get("/api/usuarios/", headers=headers_admin)
        # 200 o 500 (mock de BD), pero NO 401 ni 403
        assert response.status_code not in [401, 403]

    def test_formato_token_incorrecto_retorna_401(self, client):
        # Sin prefijo "Bearer"
        response = client.get(
            "/api/usuarios/",
            headers={"Authorization": "token-sin-bearer"}
        )
        assert response.status_code in [401, 403]
