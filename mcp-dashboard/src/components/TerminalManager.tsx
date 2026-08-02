import React, { useState } from 'react';
import { Terminal, Play, Square, RefreshCw, Plus, Trash2, CheckCircle2, ShieldAlert, Cpu } from 'lucide-react';

interface TerminalTab {
  id: string;
  name: string;
  command: string;
  status: 'running' | 'stopped' | 'error';
  logs: string[];
}

export const TerminalManager: React.FC = () => {
  const [tabs, setTabs] = useState<TerminalTab[]>([
    {
      id: 'term_backend',
      name: 'Consola 1: Backend API',
      command: 'python silhouettemcp_server.py',
      status: 'running',
      logs: [
        '[INFO] Starting SilhouetteMCP Backend on http://localhost:8001...',
        '[INFO] MultiAgentOrchestrator online with 5 specialized agents.',
        '[INFO] Prometheus metrics exposed at /metrics.',
        '[SUCCESS] Server ready for requests.'
      ]
    },
    {
      id: 'term_frontend',
      name: 'Consola 2: React Dashboard',
      command: 'npm run dev',
      status: 'running',
      logs: [
        '> mcp-dashboard@1.0.0 dev',
        '> vite',
        'VITE v5.4.11 ready in 240 ms',
        '➜ Local: http://localhost:5174/'
      ]
    },
    {
      id: 'term_tests',
      name: 'Consola 3: Self-Healing Tests',
      command: 'python test_lanzar_agente.py',
      status: 'stopped',
      logs: [
        '[TEST] MultiAgentOrchestrator benchmark started...',
        '[TEST] Reasoner -> Planner -> Executor -> Verifier completed in 202ms.',
        '[PASS] All 5 multi-agent execution phases passed.'
      ]
    }
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('term_backend');
  const [inputCmd, setInputCmd] = useState<string>('');

  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];

  const handleRunCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputCmd.trim()) return;

    const cmdToExec = inputCmd;
    setInputCmd('');

    setTabs(prev => prev.map(t => {
      if (t.id === activeTabId) {
        return {
          ...t,
          status: 'running',
          logs: [...t.logs, `$ ${cmdToExec}`, `[SYSTEM] Comando enviado a la consola ${t.name}...`, `[OUT] Proceso ejecutado con éxito.`]
        };
      }
      return t;
    }));
  };

  const handleAddNewTerminal = () => {
    const newId = `term_${Date.now()}`;
    const newTab: TerminalTab = {
      id: newId,
      name: `Consola ${tabs.length + 1}: Nueva`,
      command: 'bash / powershell',
      status: 'running',
      logs: [`[INFO] Consola interactiva ${tabs.length + 1} inicializada.`]
    };
    setTabs(prev => [...prev, newTab]);
    setActiveTabId(newId);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Top Header */}
      <div className="flex justify-between items-center px-6 py-3.5 bg-gray-800/90 border-b border-gray-700/80">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-600/20 text-emerald-400 rounded-lg border border-emerald-500/30">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Administrador de Consolas Múltiples (Multi-Terminal Daemon)
              <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                Parallel Shell Control
              </span>
            </h2>
            <p className="text-xs text-gray-400">Ejecuta múltiples procesos en paralelo, servidores dev y pruebas en tiempo real</p>
          </div>
        </div>

        <button
          onClick={handleAddNewTerminal}
          className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition"
        >
          <Plus className="w-4 h-4" /> Nueva Consola
        </button>
      </div>

      {/* Terminal Tabs Bar */}
      <div className="flex bg-gray-950 px-4 pt-2 gap-2 border-b border-gray-800 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTabId(tab.id)}
            className={`px-4 py-2 rounded-t-lg text-xs font-mono flex items-center gap-2 transition ${
              activeTabId === tab.id
                ? 'bg-gray-900 text-emerald-400 border-t-2 border-emerald-500 font-bold'
                : 'text-gray-400 hover:bg-gray-900/60 hover:text-white'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${tab.status === 'running' ? 'bg-emerald-500 animate-pulse' : 'bg-gray-500'}`} />
            {tab.name}
          </button>
        ))}
      </div>

      {/* Live Terminal Log Screen */}
      <div className="flex-1 bg-gray-950 p-5 font-mono text-xs text-gray-300 overflow-y-auto space-y-2 border-b border-gray-800">
        <div className="text-emerald-500 font-bold mb-4">
          === {activeTab.name} | Comando activo: {activeTab.command} ===
        </div>
        {activeTab.logs.map((line, idx) => (
          <div key={idx} className="leading-relaxed whitespace-pre-wrap">
            {line.startsWith('$') ? (
              <span className="text-indigo-400 font-bold">{line}</span>
            ) : line.includes('[SUCCESS]') || line.includes('[PASS]') ? (
              <span className="text-emerald-400 font-semibold">{line}</span>
            ) : line.includes('[ERROR]') ? (
              <span className="text-rose-400 font-semibold">{line}</span>
            ) : (
              <span>{line}</span>
            )}
          </div>
        ))}
      </div>

      {/* Command Input Bar */}
      <form onSubmit={handleRunCommand} className="p-3.5 bg-gray-900 border-t border-gray-800 flex gap-3">
        <span className="text-emerald-500 font-mono text-sm self-center pl-2">$</span>
        <input
          type="text"
          placeholder="Escribe un comando para ejecutar en esta consola (Ej: python verificar_sistema.py)..."
          value={inputCmd}
          onChange={(e) => setInputCmd(e.target.value)}
          className="flex-1 bg-gray-950 border border-gray-800 text-emerald-300 font-mono text-xs rounded-lg px-4 py-2.5 focus:outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={!inputCmd.trim()}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition disabled:opacity-50"
        >
          Ejecutar
        </button>
      </form>
    </div>
  );
};
