"""Tests de la superficie HTTP real.

Cada test corresponde a un ataque que funcionaba antes del arreglo. Se ejercitan
contra la aplicación FastAPI completa, no contra los módulos por separado, para
comprobar que el endpoint —y no sólo la función interna— está protegido.
"""
from __future__ import annotations

import os
import sys

import pytest

pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient  # noqa: E402

ADMIN_EMAIL = "admin@pruebas.test"
ADMIN_PASSWORD = "contraseña-de-pruebas-2026"


@pytest.fixture(scope="module")
def client() -> TestClient:
    from backend.app.security.auth import hash_password

    os.environ["SILHOUETTE_ADMIN_EMAIL"] = ADMIN_EMAIL
    os.environ["SILHOUETTE_ADMIN_PASSWORD_HASH"] = hash_password(
        ADMIN_PASSWORD, iterations=1_000
    )
    # El servidor lee el entorno al importarse.
    sys.modules.pop("silhouettemcp_server", None)
    import silhouettemcp_server as servidor

    return TestClient(servidor.app)


@pytest.fixture()
def token(client: TestClient) -> str:
    respuesta = client.post(
        "/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["token"]


@pytest.fixture()
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestEndpointsPeligrososProtegidos:
    """Los tres endpoints que formaban la cadena de compromiso del equipo."""

    def test_lectura_de_archivos_exige_credenciales(self, client: TestClient) -> None:
        r = client.get("/api/system/file-content", params={"path": "README.md"})
        assert r.status_code in (401, 403), "la lectura de archivos estaba abierta"

    def test_escritura_de_archivos_exige_credenciales(self, client: TestClient) -> None:
        r = client.post("/api/system/save-file", json={"path": "x.txt", "content": "y"})
        assert r.status_code in (401, 403), "la escritura de archivos estaba abierta"

    def test_lanzar_procesos_exige_credenciales(self, client: TestClient) -> None:
        r = client.post("/api/system/os-launch", json={"app_name": "calc"})
        assert r.status_code in (401, 403), "el lanzamiento de procesos estaba abierto"

    @pytest.mark.parametrize(
        "metodo,ruta,cuerpo",
        [
            ("post", "/api/agents/deploy", {}),
            ("post", "/api/agents/stop", {}),
            ("post", "/api/system/credentials", {}),
            ("get", "/api/system/credentials", None),
            ("post", "/api/mcp/create-server", {"name": "x"}),
            ("delete", "/api/dynamic/cualquiera", None),
            ("post", "/api/system/backup", None),
        ],
    )
    def test_operaciones_sensibles_exigen_credenciales(
        self, client: TestClient, metodo: str, ruta: str, cuerpo: dict | None
    ) -> None:
        kwargs = {"json": cuerpo} if cuerpo is not None else {}
        r = getattr(client, metodo)(ruta, **kwargs)
        assert r.status_code in (401, 403), f"{metodo.upper()} {ruta} estaba abierto"


class TestConfinamientoDeRutas:
    """Con credenciales válidas, la ruta sigue confinada al workspace."""

    @pytest.mark.parametrize(
        "ruta",
        ["../../../etc/passwd", "../../fuera.txt", ".env", "security/master.key"],
    )
    def test_no_se_puede_leer_fuera_del_workspace(
        self, client: TestClient, auth: dict[str, str], ruta: str
    ) -> None:
        r = client.get("/api/system/file-content", params={"path": ruta}, headers=auth)
        assert r.status_code == 403, f"se pudo leer {ruta}"

    def test_no_se_puede_escribir_fuera_del_workspace(
        self, client: TestClient, auth: dict[str, str]
    ) -> None:
        r = client.post(
            "/api/system/save-file",
            json={"path": "../../../tmp/intruso.txt", "content": "x"},
            headers=auth,
        )
        assert r.status_code == 403

    def test_se_puede_leer_dentro_del_workspace(
        self, client: TestClient, auth: dict[str, str]
    ) -> None:
        r = client.get("/api/system/file-content", params={"path": "README.md"}, headers=auth)
        assert r.status_code == 200
        assert r.json()["success"] is True


class TestListaBlancaDeProcesos:
    def test_sin_lista_blanca_no_se_lanza_nada(
        self, client: TestClient, auth: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SILHOUETTE_ALLOWED_APPS", raising=False)
        r = client.post("/api/system/os-launch", json={"app_name": "calc"}, headers=auth)
        assert r.status_code == 403
        assert "desactivado" in r.json()["detail"]

    def test_rechaza_ruta_absoluta(
        self, client: TestClient, auth: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SILHOUETTE_ALLOWED_APPS", "notepad")
        ruta = r"C:\Windows\System32\calc.exe" if sys.platform == "win32" else "/bin/sh"
        r = client.post("/api/system/os-launch", json={"app_name": ruta}, headers=auth)
        assert r.status_code == 403


class TestAutenticacion:
    def test_login_correcto_devuelve_token(self, client: TestClient) -> None:
        r = client.post(
            "/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert r.status_code == 200
        cuerpo = r.json()
        assert cuerpo["token"]
        assert ADMIN_PASSWORD not in cuerpo["token"]

    def test_login_incorrecto_rechazado(self, client: TestClient) -> None:
        r = client.post("/admin/login", json={"email": ADMIN_EMAIL, "password": "mala"})
        assert r.status_code == 401

    def test_el_token_antiguo_basico_ya_no_sirve(self, client: TestClient) -> None:
        # El esquema anterior aceptaba base64(email:contraseña) como token.
        import base64

        antiguo = base64.b64encode(f"{ADMIN_EMAIL}:{ADMIN_PASSWORD}".encode()).decode()
        r = client.get(
            "/api/system/file-content",
            params={"path": "README.md"},
            headers={"Authorization": f"Bearer {antiguo}"},
        )
        assert r.status_code == 401

    def test_logout_revoca_el_token(self, client: TestClient, token: str) -> None:
        cabeceras = {"Authorization": f"Bearer {token}"}
        assert client.post("/admin/logout", headers=cabeceras).status_code == 200
        r = client.get("/api/system/file-content", params={"path": "README.md"}, headers=cabeceras)
        assert r.status_code == 401


class TestEndpointsPublicos:
    """Lo que debe seguir siendo accesible sin credenciales."""

    @pytest.mark.parametrize("ruta", ["/", "/health", "/metrics/public"])
    def test_siguen_abiertos(self, client: TestClient, ruta: str) -> None:
        assert client.get(ruta).status_code == 200

    def test_el_guardian_de_inyeccion_es_publico(self, client: TestClient) -> None:
        r = client.post("/api/security/guard", json={"text": "Hola, ¿cómo estás?"})
        assert r.status_code == 200
        assert r.json()["safe"] is True
