/**
 * Punto único de configuración de la API.
 *
 * Antes había 17 apariciones de `http://localhost:8001` escritas a mano en 8
 * componentes y ningún uso de `import.meta.env`, así que el dashboard no podía
 * desplegarse fuera de la máquina de desarrollo sin editar el código.
 *
 * Configure el destino con `VITE_API_BASE_URL` en un archivo `.env.local`:
 *
 *     VITE_API_BASE_URL=https://silhouette.ejemplo.com
 */

const DEFAULT_API_BASE = "http://localhost:8001";

/** URL base del backend, sin barra final. */
export const API_BASE: string = (
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE
).replace(/\/+$/, "");

/** URL base de Ollama para el descubrimiento de modelos locales. */
export const OLLAMA_BASE: string = (
  import.meta.env.VITE_OLLAMA_BASE_URL ?? "http://localhost:11434"
).replace(/\/+$/, "");

/** Construye una URL absoluta de la API a partir de una ruta. */
export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

/** URL del WebSocket de streaming, derivada de la base HTTP. */
export function wsUrl(path: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

/** Token de sesión emitido por `/admin/login`. */
const TOKEN_KEY = "silhouette.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * `fetch` con la URL base y la cabecera de autorización ya aplicadas.
 *
 * Lanza un error con el detalle del backend cuando la respuesta no es 2xx, de
 * modo que quien llama no tenga que distinguir "falló" de "devolvió un cuerpo
 * de error con estado 200".
 */
export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(apiUrl(path), { ...init, headers });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // La respuesta no era JSON; se conserva el estado como detalle.
    }
    if (response.status === 401) {
      clearToken();
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
