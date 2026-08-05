import { useState, useEffect, useCallback } from "react";
import {
  FolderGit2,
  GitBranch,
  Plus,
  Check,
  Terminal,
  Download,
  RefreshCw,
  Layers,
} from "lucide-react";
import { apiFetch, getToken } from "@/lib/api";

/**
 * Proyectos, ramas y agentes CLI.
 *
 * Tres cosas que sólo se podían hacer por línea de comandos y ahora se hacen
 * desde la app: registrar carpetas locales sobre las que trabajar, gestionar
 * sus ramas, e instalar y autenticar los agentes CLI.
 *
 * Sobre el login: el flujo OAuth necesita una terminal y el navegador del
 * usuario, así que el botón **abre una terminal real** con el comando puesto.
 * No se piden credenciales ni se simula el inicio de sesión — el sistema nunca
 * debe manejar contraseñas de terceros.
 */

interface Project {
  id: string;
  name: string;
  path: string;
  is_git: boolean;
  exists: boolean;
  description: string;
}

interface Branch {
  name: string;
  sha: string;
  last_commit: string;
  current: boolean;
  is_workspace: boolean;
}

interface CliEntry {
  cli: string;
  label: string;
  installed: boolean;
  executable: string | null;
  installable: boolean;
  install_manager: string | null;
  docs_url: string;
  login: { hint: string; command: string; opens_browser: boolean; supported: boolean };
}

interface WorkspaceEntry {
  task_id: string;
  agent: string;
  branch: string;
  base_branch: string;
  integrated: boolean;
}

function Card({
  title,
  icon: Icon,
  children,
  action,
}: {
  title: string;
  icon: typeof FolderGit2;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <header className="flex items-center justify-between mb-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <Icon className="w-4 h-4 text-gray-500" />
          {title}
        </h3>
        {action}
      </header>
      {children}
    </section>
  );
}

export function ProjectsPanel() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [currentBranch, setCurrentBranch] = useState("");
  const [workspaces, setWorkspaces] = useState<WorkspaceEntry[]>([]);
  const [clis, setClis] = useState<CliEntry[]>([]);
  const [newPath, setNewPath] = useState("");
  const [newBranch, setNewBranch] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const requireAuth = (): boolean => {
    if (getToken()) return true;
    setError("Esta acción requiere iniciar sesión como administrador.");
    return false;
  };

  const loadProjects = useCallback(async () => {
    try {
      const d = await apiFetch<{ projects: Project[]; active: string | null }>("/api/projects");
      setProjects(d.projects);
      setActiveId(d.active);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  const loadBranches = useCallback(async (projectId: string | null) => {
    if (!projectId) return;
    try {
      const d = await apiFetch<{ current: string; branches: Branch[] }>(
        `/api/branches?project_id=${encodeURIComponent(projectId)}`,
      );
      setBranches(d.branches);
      setCurrentBranch(d.current);
    } catch {
      // Un proyecto sin git no tiene ramas: no es un error que mostrar.
      setBranches([]);
      setCurrentBranch("");
    }
  }, []);

  const loadClis = useCallback(async () => {
    try {
      setClis((await apiFetch<{ clis: CliEntry[] }>("/api/cli/catalog")).clis);
    } catch {
      setClis([]);
    }
  }, []);

  const loadWorkspaces = useCallback(async () => {
    try {
      setWorkspaces((await apiFetch<{ workspaces: WorkspaceEntry[] }>("/api/workspaces")).workspaces);
    } catch {
      setWorkspaces([]);
    }
  }, []);

  useEffect(() => {
    loadProjects();
    loadClis();
    loadWorkspaces();
  }, [loadProjects, loadClis, loadWorkspaces]);

  useEffect(() => {
    loadBranches(activeId);
  }, [activeId, loadBranches]);

  const act = async (label: string, fn: () => Promise<void>) => {
    setBusy(label);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  };

  const registerProject = () =>
    act("register", async () => {
      if (!requireAuth() || !newPath.trim()) return;
      await apiFetch("/api/projects", {
        method: "POST",
        body: JSON.stringify({ path: newPath.trim() }),
      });
      setNewPath("");
      await loadProjects();
    });

  const activate = (id: string) =>
    act(`activate-${id}`, async () => {
      if (!requireAuth()) return;
      await apiFetch(`/api/projects/${id}/activate`, { method: "POST" });
      await loadProjects();
    });

  const createBranch = () =>
    act("branch", async () => {
      if (!requireAuth() || !newBranch.trim() || !activeId) return;
      await apiFetch("/api/branches", {
        method: "POST",
        body: JSON.stringify({ name: newBranch.trim(), project_id: activeId }),
      });
      setNewBranch("");
      await loadBranches(activeId);
    });

  const switchBranch = (name: string) =>
    act(`switch-${name}`, async () => {
      if (!requireAuth() || !activeId) return;
      await apiFetch("/api/branches/switch", {
        method: "POST",
        body: JSON.stringify({ name, project_id: activeId }),
      });
      await loadBranches(activeId);
    });

  const installCli = (cli: string) =>
    act(`install-${cli}`, async () => {
      if (!requireAuth()) return;
      const r = await apiFetch<{ installed: boolean; detail: string; next_step?: string }>(
        `/api/cli/install/${cli}`,
        { method: "POST" },
      );
      setNotice(`${r.detail} ${r.next_step ?? ""}`.trim());
      await loadClis();
    });

  const loginCli = (cli: string) =>
    act(`login-${cli}`, async () => {
      if (!requireAuth()) return;
      const r = await apiFetch<{ opened: boolean; detail: string; next_step?: string }>(
        `/api/cli/login/${cli}`,
        { method: "POST" },
      );
      setNotice(`${r.detail} ${r.next_step ?? ""}`.trim());
    });

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-800">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proyectos */}
        <Card
          title="Proyectos"
          icon={FolderGit2}
          action={
            <button
              onClick={loadProjects}
              className="px-2.5 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200"
            >
              <RefreshCw className="w-3 h-3 inline" />
            </button>
          }
        >
          <div className="flex gap-2 mb-4">
            <input
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && registerProject()}
              placeholder="C:/ruta/a/tu/proyecto"
              className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
            <button
              onClick={registerProject}
              disabled={busy === "register" || !newPath.trim()}
              className="px-3 py-1.5 text-sm rounded-md bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          <ul className="space-y-2">
            {projects.map((p) => (
              <li
                key={p.id}
                className={`flex items-start justify-between gap-3 p-2.5 rounded-md border ${
                  p.id === activeId ? "border-teal-300 bg-teal-50" : "border-gray-100"
                }`}
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 flex items-center gap-2">
                    {p.name}
                    {p.is_git && <GitBranch className="w-3 h-3 text-gray-400" />}
                    {!p.exists && (
                      <span className="text-xs text-rose-600">(carpeta no encontrada)</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{p.path}</p>
                </div>
                {p.id === activeId ? (
                  <span className="text-xs text-teal-700 font-medium shrink-0 flex items-center gap-1">
                    <Check className="w-3 h-3" /> activo
                  </span>
                ) : (
                  <button
                    onClick={() => activate(p.id)}
                    disabled={busy === `activate-${p.id}`}
                    className="text-xs text-gray-600 hover:text-gray-900 shrink-0"
                  >
                    activar
                  </button>
                )}
              </li>
            ))}
            {projects.length === 0 && (
              <li className="text-sm text-gray-400 italic">
                Ningún proyecto registrado. Añada la ruta de una carpeta local.
              </li>
            )}
          </ul>
        </Card>

        {/* Ramas */}
        <Card title={`Ramas${currentBranch ? ` · ${currentBranch}` : ""}`} icon={GitBranch}>
          {activeId && branches.length > 0 ? (
            <>
              <div className="flex gap-2 mb-4">
                <input
                  value={newBranch}
                  onChange={(e) => setNewBranch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && createBranch()}
                  placeholder="feature/nueva-rama"
                  className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <button
                  onClick={createBranch}
                  disabled={busy === "branch" || !newBranch.trim()}
                  className="px-3 py-1.5 text-sm rounded-md bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <ul className="space-y-1.5">
                {branches.map((b) => (
                  <li key={b.name} className="flex items-center justify-between gap-3 text-sm">
                    <span className="flex items-center gap-2 min-w-0">
                      <span className={b.current ? "font-medium text-teal-700" : "text-gray-900"}>
                        {b.name}
                      </span>
                      {b.is_workspace && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                          agente
                        </span>
                      )}
                    </span>
                    <span className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-gray-400">{b.last_commit}</span>
                      {!b.current && (
                        <button
                          onClick={() => switchBranch(b.name)}
                          disabled={busy === `switch-${b.name}`}
                          className="text-xs text-gray-600 hover:text-gray-900"
                        >
                          cambiar
                        </button>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-gray-400 italic">
              {activeId
                ? "El proyecto activo no es un repositorio git."
                : "Seleccione un proyecto para ver sus ramas."}
            </p>
          )}
        </Card>
      </div>

      {/* Espacios de trabajo de los agentes */}
      {workspaces.length > 0 && (
        <Card title="Espacios de trabajo aislados" icon={Layers}>
          <ul className="space-y-1.5">
            {workspaces.map((w) => (
              <li key={w.task_id} className="flex items-center justify-between gap-3 text-sm">
                <span className="text-gray-900">
                  {w.agent} <span className="text-gray-400">·</span>{" "}
                  <code className="text-xs text-gray-600">{w.branch}</code>
                </span>
                <span className="text-xs text-gray-500">
                  sobre {w.base_branch} · {w.integrated ? "integrado" : "en curso"}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Agentes CLI */}
      <Card
        title="Agentes de línea de comandos"
        icon={Terminal}
        action={
          <button
            onClick={loadClis}
            className="px-2.5 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200"
          >
            <RefreshCw className="w-3 h-3 inline" />
          </button>
        }
      >
        <p className="text-xs text-gray-500 mb-4">
          «Iniciar sesión» abre una terminal en su equipo con el comando puesto. El sistema
          nunca pide ni almacena sus credenciales — la autenticación ocurre en su navegador.
        </p>
        <ul className="space-y-2">
          {clis.map((c) => (
            <li
              key={c.cli}
              className="flex items-center justify-between gap-3 p-2.5 rounded-md border border-gray-100"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-900">{c.label}</p>
                <p className="text-xs text-gray-500 truncate">
                  {c.installed ? c.executable : c.login.hint}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {c.installed ? (
                  <>
                    <span className="text-xs text-emerald-600">instalado</span>
                    {c.login.opens_browser && (
                      <button
                        onClick={() => loginCli(c.cli)}
                        disabled={busy === `login-${c.cli}`}
                        className="px-2.5 py-1 text-xs rounded-md bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50"
                      >
                        {busy === `login-${c.cli}` ? "abriendo…" : "iniciar sesión"}
                      </button>
                    )}
                  </>
                ) : c.installable ? (
                  <button
                    onClick={() => installCli(c.cli)}
                    disabled={busy === `install-${c.cli}`}
                    className="px-2.5 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Download className="w-3 h-3" />
                    {busy === `install-${c.cli}` ? "instalando…" : `instalar (${c.install_manager})`}
                  </button>
                ) : (
                  <a
                    href={c.docs_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-gray-500 hover:text-gray-900 underline"
                  >
                    instalación manual
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
