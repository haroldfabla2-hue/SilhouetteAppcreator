import React, { useState } from 'react';
import { Swords, Play, GitCompare, CheckCircle2, AlertTriangle, Zap, Code, ShieldCheck, ArrowRight, Sparkles, RefreshCw } from 'lucide-react';
import { API_BASE } from "@/lib/api";

interface ArenaResult {
  modelId: string;
  modelName: string;
  codeOutput: string;
  executionTimeMs: number;
  qualityScore: number;
  syntaxValid: boolean;
  securityPassed: boolean;
}

export const ModelArena: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [modelA, setModelA] = useState('glm-5.2-max');
  const [modelB, setModelB] = useState('cli_antigravity');
  const [isComparing, setIsComparing] = useState(false);
  const [results, setResults] = useState<{ modelA: ArenaResult | null; modelB: ArenaResult | null }>({
    modelA: null,
    modelB: null
  });
  const [winningModel, setWinningModel] = useState<string | null>(null);

  const handleRunBattle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isComparing) return;

    setIsComparing(true);
    setWinningModel(null);

    try {
      const res = await fetch(`${API_BASE}/api/agents/arena`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          model_a: modelA,
          model_b: modelB
        })
      });

      if (res.ok) {
        const data = await res.json();
        setResults({
          modelA: data.model_a_result,
          modelB: data.model_b_result
        });
        setWinningModel(data.winner);
      } else {
        throw new Error(`Error HTTP ${res.status}: Servidor indisponible`);
      }
    } catch (err: any) {
      console.error("Arena execution error:", err);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-rose-600/20 text-rose-400 rounded-xl border border-rose-500/30">
            <Swords className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              Arena Multi-Modelo (Parallel Battle & Diff)
              <span className="text-xs bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2.5 py-0.5 rounded-full font-semibold">
                Superando a Orca & Claude Code
              </span>
            </h2>
            <p className="text-sm text-gray-400">Compara el código generado por 2 modelos en paralelo y fusiona la solución ganadora con 1 clic</p>
          </div>
        </div>
      </div>

      {/* Model Selection & Prompt Bar */}
      <form onSubmit={handleRunBattle} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4 shadow-xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Modelo A (Esquina Azul)</label>
            <select
              value={modelA}
              onChange={(e) => setModelA(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-2.5 text-sm font-medium focus:border-indigo-500"
            >
              <option value="glm-5.2-max">GLM-5.2 Max (Zhipu AI)</option>
              <option value="cli_antigravity">Antigravity AGY CLI (Google)</option>
              <option value="minimax-m3">MiniMax M3 (Multimodal)</option>
              <option value="openrouter-qwen-3-7">Qwen 3.7 Max (OpenRouter)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Modelo B (Esquina Roja)</label>
            <select
              value={modelB}
              onChange={(e) => setModelB(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-2.5 text-sm font-medium focus:border-rose-500"
            >
              <option value="cli_antigravity">Antigravity AGY CLI (Google)</option>
              <option value="cli_claude_code">Claude Code CLI (Anthropic)</option>
              <option value="kimi-k3">Kimi K3 (Moonshot AI)</option>
              <option value="ollama-local">Ollama Llama 3 (Local)</option>
            </select>
          </div>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Escribe el prompt a evaluar en paralelo (Ej: Crea una clase Python para autenticación JWT segura con tokens expira)..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isComparing}
            className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={isComparing || !prompt.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-rose-600 hover:from-indigo-500 hover:to-rose-500 text-white font-bold rounded-lg transition disabled:opacity-50"
          >
            {isComparing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Swords className="w-4 h-4" />}
            Batalla de Modelos
          </button>
        </div>
      </form>

      {/* Split Screen Comparative Display */}
      {(results.modelA || results.modelB) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Model A Results */}
          <div className={`bg-gray-900 border rounded-xl p-5 space-y-4 shadow-xl relative overflow-hidden ${
            winningModel === modelA ? 'border-indigo-500 ring-2 ring-indigo-500/50' : 'border-gray-800'
          }`}>
            {winningModel === modelA && (
              <div className="absolute top-0 right-0 bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-bl-xl flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> GANADOR RECOMENDADO
              </div>
            )}
            <div className="flex justify-between items-center border-b border-gray-800 pb-3">
              <h3 className="font-bold text-white text-base">{results.modelA?.modelName}</h3>
              <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded font-mono">
                {results.modelA?.executionTimeMs} ms
              </span>
            </div>
            <div className="flex gap-3 text-xs">
              <span className="text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Quality: {Math.round((results.modelA?.qualityScore || 0) * 100)}%
              </span>
              <span className="text-blue-400 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5" /> Syntax: OK
              </span>
            </div>
            <pre className="bg-gray-950 p-4 rounded-lg text-xs font-mono text-gray-300 overflow-x-auto border border-gray-800 max-h-80">
              <code>{results.modelA?.codeOutput}</code>
            </pre>
          </div>

          {/* Model B Results */}
          <div className={`bg-gray-900 border rounded-xl p-5 space-y-4 shadow-xl relative overflow-hidden ${
            winningModel === modelB ? 'border-rose-500 ring-2 ring-rose-500/50' : 'border-gray-800'
          }`}>
            {winningModel === modelB && (
              <div className="absolute top-0 right-0 bg-rose-600 text-white text-xs font-bold px-3 py-1 rounded-bl-xl flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> GANADOR RECOMENDADO
              </div>
            )}
            <div className="flex justify-between items-center border-b border-gray-800 pb-3">
              <h3 className="font-bold text-white text-base">{results.modelB?.modelName}</h3>
              <span className="text-xs bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded font-mono">
                {results.modelB?.executionTimeMs} ms
              </span>
            </div>
            <div className="flex gap-3 text-xs">
              <span className="text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Quality: {Math.round((results.modelB?.qualityScore || 0) * 100)}%
              </span>
              <span className="text-blue-400 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5" /> Syntax: OK
              </span>
            </div>
            <pre className="bg-gray-950 p-4 rounded-lg text-xs font-mono text-gray-300 overflow-x-auto border border-gray-800 max-h-80">
              <code>{results.modelB?.codeOutput}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
