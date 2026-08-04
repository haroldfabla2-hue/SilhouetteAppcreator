"""Tests de autenticación de administrador."""
from __future__ import annotations

import time

import pytest

from backend.app.security.auth import (
    AuthNotConfigured,
    AuthService,
    hash_password,
    verify_password,
)

PASSWORD = "una-contraseña-larga-y-única-2026"
EMAIL = "admin@ejemplo.test"


@pytest.fixture()
def service() -> AuthService:
    # Iteraciones bajas para no penalizar la suite; la producción usa 600k.
    return AuthService(EMAIL, hash_password(PASSWORD, iterations=1_000))


class TestHashing:
    def test_verifica_la_contraseña_correcta(self) -> None:
        assert verify_password(PASSWORD, hash_password(PASSWORD, iterations=1_000))

    def test_rechaza_la_contraseña_incorrecta(self) -> None:
        assert not verify_password("otra", hash_password(PASSWORD, iterations=1_000))

    def test_la_sal_hace_los_hashes_distintos(self) -> None:
        a = hash_password(PASSWORD, iterations=1_000)
        b = hash_password(PASSWORD, iterations=1_000)
        assert a != b, "sin sal, dos hashes iguales permitirían tablas arcoíris"

    def test_el_hash_no_contiene_la_contraseña(self) -> None:
        assert PASSWORD not in hash_password(PASSWORD, iterations=1_000)

    @pytest.mark.parametrize("malformado", ["", "sin-dolares", "md5$1$a$b", "pbkdf2_sha256$x$y"])
    def test_los_hashes_malformados_no_validan(self, malformado: str) -> None:
        assert not verify_password(PASSWORD, malformado)


class TestLogin:
    def test_el_login_correcto_emite_un_token(self, service: AuthService) -> None:
        token = service.login(EMAIL, PASSWORD)
        assert service.resolve(token).email == EMAIL

    def test_el_token_no_deriva_de_la_contraseña(self, service: AuthService) -> None:
        # El esquema anterior codificaba email:contraseña en base64.
        import base64

        token = service.login(EMAIL, PASSWORD)
        decodificable = base64.b64encode(f"{EMAIL}:{PASSWORD}".encode()).decode()
        assert token != decodificable
        assert PASSWORD not in token

    def test_dos_logins_dan_tokens_distintos(self, service: AuthService) -> None:
        assert service.login(EMAIL, PASSWORD) != service.login(EMAIL, PASSWORD)

    def test_contraseña_incorrecta_rechazada(self, service: AuthService) -> None:
        with pytest.raises(PermissionError):
            service.login(EMAIL, "incorrecta")

    def test_correo_incorrecto_rechazado(self, service: AuthService) -> None:
        with pytest.raises(PermissionError):
            service.login("otro@ejemplo.test", PASSWORD)

    def test_el_correo_no_distingue_mayusculas(self, service: AuthService) -> None:
        assert service.login(EMAIL.upper(), PASSWORD)


class TestFallaEnCerrado:
    def test_sin_configuracion_no_se_puede_entrar(self) -> None:
        vacio = AuthService("", "")
        assert not vacio.is_configured
        with pytest.raises(AuthNotConfigured):
            vacio.login(EMAIL, PASSWORD)

    def test_un_token_inventado_no_vale(self, service: AuthService) -> None:
        with pytest.raises(PermissionError):
            service.resolve("token-inventado")

    def test_token_vacio_rechazado(self, service: AuthService) -> None:
        with pytest.raises(PermissionError):
            service.resolve("")


class TestSesiones:
    def test_el_token_caduca(self) -> None:
        service = AuthService(EMAIL, hash_password(PASSWORD, iterations=1_000), token_ttl=0)
        token = service.login(EMAIL, PASSWORD)
        time.sleep(0.01)
        with pytest.raises(PermissionError):
            service.resolve(token)

    def test_revocar_invalida_el_token(self, service: AuthService) -> None:
        token = service.login(EMAIL, PASSWORD)
        assert service.revoke(token)
        with pytest.raises(PermissionError):
            service.resolve(token)

    def test_revocar_todo_cierra_las_sesiones(self, service: AuthService) -> None:
        service.login(EMAIL, PASSWORD)
        service.login(EMAIL, PASSWORD)
        assert service.revoke_all() == 2
        assert service.active_sessions == 0
