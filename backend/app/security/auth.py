"""Autenticación de administrador.

Sustituye a las credenciales que estaban escritas en el código fuente. Reglas:

- Las credenciales se leen del entorno, nunca del código.
- La contraseña se almacena como hash PBKDF2-HMAC-SHA256 con sal e iteraciones
  (stdlib, sin dependencias nuevas).
- El login emite un token de sesión opaco y caducable; el token NO es la
  contraseña, se puede revocar y no sirve para autenticarse dos veces si expira.
- Si no hay administrador configurado, todo endpoint protegido responde 503.
  Falla en cerrado: sin configuración no se entra, en lugar de entrar sin control.

Para generar un hash:

    python -m backend.app.security.auth "mi-contraseña"
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass

# Coste de derivación. 600k iteraciones es la recomendación OWASP 2023 para
# PBKDF2-HMAC-SHA256.
PBKDF2_ITERATIONS = 600_000
TOKEN_TTL_SECONDS = 8 * 3600

ENV_ADMIN_EMAIL = "SILHOUETTE_ADMIN_EMAIL"
ENV_ADMIN_HASH = "SILHOUETTE_ADMIN_PASSWORD_HASH"


class AuthNotConfigured(RuntimeError):
    """No hay administrador configurado en el entorno."""


def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> str:
    """Deriva un hash con sal en formato `pbkdf2_sha256$iter$sal_b64$hash_b64`."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    """Verifica una contraseña contra un hash codificado, en tiempo constante."""
    try:
        algorithm, iterations_s, salt_b64, hash_b64 = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations_s)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


@dataclass(frozen=True)
class AdminIdentity:
    email: str
    role: str = "admin"


@dataclass
class _Session:
    email: str
    expires_at: float


class AuthService:
    """Emite y valida tokens de sesión de administrador."""

    def __init__(
        self,
        admin_email: str | None = None,
        admin_password_hash: str | None = None,
        *,
        token_ttl: int = TOKEN_TTL_SECONDS,
    ) -> None:
        # Los valores explícitos ganan; si no se pasan, el entorno se consulta
        # en cada acceso. Leerlo una sola vez en el constructor congelaba la
        # configuración en el momento del import, de modo que cargar el .env
        # después (o importar el módulo antes de configurarlo) dejaba el
        # servicio permanentemente sin administrador.
        self._email_override = admin_email
        self._hash_override = admin_password_hash
        self._token_ttl = token_ttl
        self._sessions: dict[str, _Session] = {}

    @property
    def _email(self) -> str:
        if self._email_override is not None:
            return self._email_override
        return os.getenv(ENV_ADMIN_EMAIL, "")

    @property
    def _hash(self) -> str:
        if self._hash_override is not None:
            return self._hash_override
        return os.getenv(ENV_ADMIN_HASH, "")

    @property
    def is_configured(self) -> bool:
        return bool(self._email and self._hash)

    def login(self, email: str, password: str) -> str:
        """Valida credenciales y devuelve un token de sesión nuevo."""
        if not self.is_configured:
            raise AuthNotConfigured(
                f"Defina {ENV_ADMIN_EMAIL} y {ENV_ADMIN_HASH} en el entorno."
            )
        # Comparar el correo en tiempo constante evita distinguir "usuario
        # incorrecto" de "contraseña incorrecta" por tiempo de respuesta.
        email_ok = hmac.compare_digest(email.strip().lower(), self._email.strip().lower())
        password_ok = verify_password(password, self._hash)
        if not (email_ok and password_ok):
            raise PermissionError("Credenciales inválidas")

        self._purge_expired()
        token = secrets.token_urlsafe(32)
        self._sessions[token] = _Session(
            email=self._email, expires_at=time.time() + self._token_ttl
        )
        return token

    def resolve(self, token: str) -> AdminIdentity:
        """Devuelve la identidad de un token válido, o lanza PermissionError."""
        self._purge_expired()
        session = self._sessions.get(token)
        if session is None:
            raise PermissionError("Token inválido o expirado")
        return AdminIdentity(email=session.email)

    def revoke(self, token: str) -> bool:
        return self._sessions.pop(token, None) is not None

    def revoke_all(self) -> int:
        count = len(self._sessions)
        self._sessions.clear()
        return count

    @property
    def active_sessions(self) -> int:
        self._purge_expired()
        return len(self._sessions)

    def _purge_expired(self) -> None:
        now = time.time()
        for token in [t for t, s in self._sessions.items() if s.expires_at <= now]:
            del self._sessions[token]


auth_service = AuthService()


if __name__ == "__main__":  # pragma: no cover - utilidad de línea de comandos
    import sys

    if len(sys.argv) != 2:
        print('Uso: python -m backend.app.security.auth "<contraseña>"')
        raise SystemExit(2)
    print(f"{ENV_ADMIN_HASH}={hash_password(sys.argv[1])}")
