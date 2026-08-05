"""Punto de entrada del puerto 8000 — reexporta la aplicación consolidada.

Aquí vivía un **segundo servidor FastAPI** con su propia configuración de CORS,
su propio ciclo de arranque y sus propios routers sin autenticación. Mantener
dos superficies significaba aplicar cada corrección de seguridad dos veces, y
ya se había olvidado una: el CORS con comodín siguió aquí después de corregirse
en el servidor principal.

Ahora hay una sola aplicación. Este módulo la reexporta para que sigan
funcionando sin cambios:

    docker-compose.yml   ->  uvicorn main:app --port 8000
    iniciar_sistema.sh   ->  python -m uvicorn main:app --port 8000

La versión anterior está íntegra en el historial de Git:

    git log --follow -- backend/main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# El servidor consolidado vive en la raíz del repositorio.
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from silhouettemcp_server import app  # noqa: E402

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    # El puerto 8000 se conserva por compatibilidad con los despliegues
    # existentes; sirve exactamente la misma aplicación que el 8001.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
