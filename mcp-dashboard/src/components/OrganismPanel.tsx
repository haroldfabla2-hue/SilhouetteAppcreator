import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Brain,
  HeartPulse,
  GitBranch,
  Plug,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  MinusCircle,
} from "lucide-react";
import { apiFetch, getToken } from "@/lib/api";

/**
 * Panel del organismo.
 *
 * Existía un desfase que hacía imposible ver el sistema funcionando: el backend
 * expone el organismo, los motores cognitivos, la salud, git y la conexión de
 * IAs, y la interfaz no mostraba ninguno. Este panel cierra ese hueco.
 *
 * Regla de presentación, la misma que rige el backend: **«sin datos» se muestra
 * como «sin datos», nunca como cero ni como correcto.** Un indicador en blanco
 * es información; un cero inventado es una mentira.
 */

type Severity = "ok" | "degraded" | "critical" | "unknown";

interface Indicator {
  name: string;
  severity: Severity;
  detail: string;
  value: number | null;
  source: string;
}

interface HealthReport {
  severity: Severity;
  indicators: Indicator[];
  actions_suggested: string[];
}

interface Organ {
  name: string;
  runs: number;
  failures: number;
  healthy: boolean;
  enabled: boolean;
  last_error: string | null;
}

interface Vitals {
  alive: boolean;
  health: string;
  uptime_s: number;
  ticks: number;
  circadian: { phase: string; seconds_since_interaction: number; active_engines: string[] };
  homeostasis: { profile: string; reason: string; cadence_multiplier: number; max_concurrency: number };
  organs: { total: number; healthy: number; unhealthy: string[]; detail: Organ[] };
  activity: { total_runs: number; total_failures: number; failure_rate: number | null };
}

interface SetupReport {
  ready_count: number;
  has_any_llm: boolean;
  next_step: string;
  providers: Array<{ label: string; status: string; detail: string; usable: boolean }>;
  cli_agents: Array<{ label: string; available: boolean; usable: boolean | null; probe_detail: string }>;
  issues: Array<{ severity: string; summary: string; fix_hint: string; auto_fixable: boolean }>;
}

interface EngineStats {
  available: boolean;
  reason?: string;
  engines?: Record<string, { runs: number; failures: number; last_summary: string | null; interval_s: number }>;
}

const SEVERITY_STYLE: Record<Severity, { icon: typeof CheckCircle2; className: string; label: string }> = {
  ok: { icon: CheckCircle2, className: "text-emerald-600 bg-emerald-50 border-emerald-200", label: "correcto" },
  degraded: { icon: AlertTriangle, className: "text-amber-600 bg-amber-50 border-amber-200", label: "degradado" },
  critical: { icon: XCircle, className: "text-rose-600 bg-rose-50 border-rose-200", label: "crítico" },
  unknown: { icon: MinusCircle, className: "text-gray-500 bg-gray-50 border-gray-200", label: "sin datos" },
};

const PHASE_LABEL: Record<string, string> = {
  active: "Despierto — atendiendo",
  alert: "Alerta — interacción reciente",
  drowsy: "Somnoliento — introspección",
  dreaming: "Soñando — consolidando memoria",
  deep_rest: "Reposo profundo",
};

function Section({
  title,
  icon: Icon,
  children,
  action,
}: {
  title: string;
  icon: typeof Activity;
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

/** Muestra un valor que puede no estar medido. Nunca sustituye null por 0. */
function Measure({ value, suffix = "", digits = 0 }: { value: number | null | undefined; suffix?: string; digits?: number }) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">sin medir</span>;
  }
  return (
    <span className="tabular-nums">
      {value.toFixed(digits)}
      {suffix}
    </span>
  );
}

export function OrganismPanel() {
  const [vitals, setVitals] = useState<Vitals | null>(null);
  const [health, setHealth] = useState<HealthReport | null>(null);
  const [setup, setSetup] = useState<SetupReport | null>(null);
  const [engines, setEngines] = useState<EngineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState<string>("");

  const load = useCallback(async () => {
    setError("");
    try {
      // Cada consulta es independiente: si una falla, las demás siguen
      // mostrándose, y el fallo se dice en lugar de dejar el panel en blanco.
      const [v, h, e] = await Promise.allSettled([
        apiFetch<Vitals>("/api/organism/vitals"),
        apiFetch<HealthReport>("/api/health/diagnose"),
        apiFetch<EngineStats>("/api/cognition/engines"),
      ]);
      if (v.status === "fulfilled") setVitals(v.value);
      if (h.status === "fulfilled") setHealth(h.value);
      if (e.status === "fulfilled") setEngines(e.value);

      const fallos = [v, h, e].filter((r) => r.status === "rejected");
      if (fallos.length === 3) {
        setError("No se pudo contactar con el backend. ¿Está arrancado en el puerto configurado?");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSetup = useCallback(async () => {
    try {
      // El sondeo ejecuta cada CLI de verdad, así que tarda; va aparte.
      setSetup(await apiFetch<SetupReport>("/api/setup/status"));
    } catch (e) {
      setSetup(null);
    }
  }, []);

  useEffect(() => {
    load();
    loadSetup();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load, loadSetup]);

  const act = async (label: string, path: string) => {
    if (!getToken()) {
      setError("Esta acción requiere iniciar sesión como administrador.");
      return;
    }
    setBusy(label);
    setError("");
    try {
      await apiFetch(path, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  };

  if (loading) {
    return <div className="p-8 text-sm text-gray-500">Consultando el organismo…</div>;
  }

  const globalSeverity: Severity = health?.severity ?? "unknown";
  const style = SEVERITY_STYLE[globalSeverity];
  const GlobalIcon = style.icon;

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* Estado general */}
      <div className={`rounded-lg border p-6 ${style.className}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <GlobalIcon className="w-6 h-6 mt-0.5 shrink-0" />
            <div>
              <p className="text-lg font-semibold">Estado del sistema: {style.label}</p>
              <p className="text-sm opacity-90 mt-1">
                {vitals?.alive
                  ? `Vivo · ${PHASE_LABEL[vitals.circadian.phase] ?? vitals.circadian.phase} · ${vitals.ticks} latidos`
                  : "El organismo no está en marcha."}
              </p>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={load}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-white/70 hover:bg-white transition"
            >
              <RefreshCw className="w-3.5 h-3.5 inline mr-1" />
              Actualizar
            </button>
            <button
              onClick={() => act("awaken", vitals?.alive ? "/api/organism/rest" : "/api/organism/awaken")}
              disabled={busy === "awaken"}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-white/70 hover:bg-white transition disabled:opacity-50"
            >
              {vitals?.alive ? "Detener" : "Despertar"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Indicadores de salud */}
        <Section
          title="Diagnóstico (medido, no estimado)"
          icon={HeartPulse}
          action={
            <button
              onClick={() => act("heal", "/api/health/heal")}
              disabled={busy === "heal"}
              className="px-2.5 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
            >
              {busy === "heal" ? "Reparando…" : "Auto-sanar"}
            </button>
          }
        >
          <ul className="space-y-3">
            {(health?.indicators ?? []).map((ind) => {
              const s = SEVERITY_STYLE[ind.severity];
              const Icon = s.icon;
              return (
                <li key={ind.name} className="flex items-start gap-3">
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${s.className.split(" ")[0]}`} />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 capitalize">{ind.name}</p>
                    <p className="text-xs text-gray-600">{ind.detail}</p>
                    <p className="text-[11px] text-gray-400 mt-0.5">fuente: {ind.source}</p>
                  </div>
                </li>
              );
            })}
            {!health && <li className="text-sm text-gray-400 italic">Sin diagnóstico disponible.</li>}
          </ul>
        </Section>

        {/* Homeostasis y ritmo */}
        <Section title="Homeostasis y ritmo circadiano" icon={Activity}>
          {vitals ? (
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-gray-600">Perfil de recursos</dt>
                <dd className="font-medium text-gray-900">{vitals.homeostasis.profile}</dd>
              </div>
              <p className="text-xs text-gray-500 -mt-1">{vitals.homeostasis.reason}</p>
              <div className="flex justify-between gap-4">
                <dt className="text-gray-600">Cadencia</dt>
                <dd className="font-medium">×{vitals.homeostasis.cadence_multiplier}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-gray-600">Concurrencia máxima</dt>
                <dd className="font-medium">{vitals.homeostasis.max_concurrency}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-gray-600">Fase</dt>
                <dd className="font-medium">{PHASE_LABEL[vitals.circadian.phase] ?? vitals.circadian.phase}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-gray-600">Tasa de fallo</dt>
                <dd className="font-medium">
                  <Measure
                    value={vitals.activity.failure_rate !== null ? vitals.activity.failure_rate * 100 : null}
                    suffix="%"
                    digits={1}
                  />
                </dd>
              </div>
              <p className="text-[11px] text-gray-400 pt-1">
                Motores activos en esta fase: {vitals.circadian.active_engines.join(", ")}
              </p>
            </dl>
          ) : (
            <p className="text-sm text-gray-400 italic">Organismo no disponible.</p>
          )}
        </Section>

        {/* Motores cognitivos */}
        <Section
          title="Motores cognitivos"
          icon={Brain}
          action={
            <button
              onClick={() => act("cognition", "/api/cognition/run-all")}
              disabled={busy === "cognition" || !engines?.available}
              className="px-2.5 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
            >
              {busy === "cognition" ? "Ejecutando…" : "Ciclo completo"}
            </button>
          }
        >
          {engines?.available ? (
            <ul className="space-y-2.5">
              {Object.entries(engines.engines ?? {}).map(([nombre, datos]) => (
                <li key={nombre} className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 capitalize">{nombre}</p>
                    <p className="text-xs text-gray-500 truncate">
                      {datos.last_summary ?? <span className="italic text-gray-400">aún no se ha ejecutado</span>}
                    </p>
                  </div>
                  <span className="text-xs text-gray-500 shrink-0 tabular-nums">
                    {datos.runs} ejec. · {datos.failures} fallos
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              No disponibles: {engines?.reason ?? "silhouette-brain no instalado"}
            </p>
          )}
        </Section>

        {/* Órganos */}
        <Section title="Órganos" icon={GitBranch}>
          {vitals ? (
            <ul className="space-y-2">
              {vitals.organs.detail.map((o) => (
                <li key={o.name} className="flex items-center justify-between gap-3 text-sm">
                  <span className="flex items-center gap-2">
                    {o.healthy ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-rose-500" />
                    )}
                    <span className={o.enabled ? "text-gray-900" : "text-gray-400 line-through"}>{o.name}</span>
                  </span>
                  <span className="text-xs text-gray-500 tabular-nums">
                    {o.runs} ejec.{o.failures > 0 && ` · ${o.failures} fallos`}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400 italic">Sin datos.</p>
          )}
        </Section>
      </div>

      {/* Conexión de IAs */}
      <Section
        title="Conexión de modelos"
        icon={Plug}
        action={
          <button
            onClick={loadSetup}
            className="px-2.5 py-1 text-xs rounded-md bg-gray-100 hover:bg-gray-200"
          >
            Volver a sondear
          </button>
        }
      >
        {setup ? (
          <>
            <div
              className={`rounded-md border p-3 mb-4 text-sm ${
                setup.has_any_llm
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-rose-200 bg-rose-50 text-rose-800"
              }`}
            >
              <p className="font-medium">
                {setup.ready_count} modelo(s) utilizable(s)
              </p>
              <p className="text-xs mt-1 opacity-90">{setup.next_step}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1.5">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Proveedores</p>
                <ul className="space-y-1">
                  {setup.providers.map((p) => (
                    <li key={p.label} className="flex items-center justify-between gap-2 text-sm">
                      <span className={p.usable ? "text-gray-900" : "text-gray-400"}>{p.label}</span>
                      <span className={`text-xs ${p.usable ? "text-emerald-600" : "text-gray-400"}`}>
                        {p.status === "ready" ? "listo" : p.status === "invalid" ? "clave inválida" : p.status === "unreachable" ? "sin conexión" : "sin configurar"}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Agentes CLI</p>
                <ul className="space-y-1">
                  {setup.cli_agents
                    .filter((a) => a.available)
                    .map((a) => (
                      <li key={a.label} className="flex items-center justify-between gap-2 text-sm">
                        <span className="text-gray-900">{a.label}</span>
                        <span className={`text-xs ${a.usable ? "text-emerald-600" : "text-amber-600"}`}>
                          {a.usable === null ? "sin comprobar" : a.usable ? "listo" : "sin sesión"}
                        </span>
                      </li>
                    ))}
                  {setup.cli_agents.filter((a) => a.available).length === 0 && (
                    <li className="text-sm text-gray-400 italic">Ninguno instalado.</li>
                  )}
                </ul>
              </div>
            </div>

            {setup.issues.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Qué falta</p>
                <ul className="space-y-2">
                  {setup.issues.slice(0, 5).map((i, n) => (
                    <li key={n} className="text-sm">
                      <span
                        className={`inline-block w-1.5 h-1.5 rounded-full mr-2 align-middle ${
                          i.severity === "blocker" ? "bg-rose-500" : "bg-amber-500"
                        }`}
                      />
                      <span className="text-gray-900">{i.summary}</span>
                      <p className="text-xs text-gray-500 ml-3.5">{i.fix_hint}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-500">
            Sondeando modelos… ejecuta cada agente de verdad, así que tarda unos segundos.
          </p>
        )}
      </Section>
    </div>
  );
}
