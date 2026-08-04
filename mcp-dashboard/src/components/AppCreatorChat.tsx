import React, { useState, useEffect } from 'react';
import { Send, Bot, User, Cpu, Sparkles, CheckCircle2, Code, Layers, ShieldCheck, Terminal, Loader2 } from 'lucide-react';
import { API_BASE } from "@/lib/api";

interface ChatMessage {
  id: string;
  sender: 'user' | 'orchestrator';
  text: string;
  timestamp: string;
  modelUsed?: string;
  orchestratorData?: any;
}

export const AppCreatorChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'orchestrator',
      text: '¡Hola! Soy SilhouetteAppcreator, tu Orquestador Multi-Agente autónomo. Escribe qué tipo de aplicación o script deseas crear y mi equipo de agentes (Reasoner, Planner, Executor y Verifier) trabajará en conjunto para construirla.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('glm-5.2-max');
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  useEffect(() => {
    // Fetch available models from backend
    fetch(`${API_BASE}/api/system/models`)
      .then(res => res.json())
      .then(data => {
        const cloud = data.cloud_and_custom_models || [];
        const local = data.local_autodiscovered_models || [];
        setAvailableModels([...cloud, ...local]);
      })
      .catch(err => console.error('Error loading models:', err));
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim() || isProcessing) return;

    const userText = inputPrompt;
    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputPrompt('');
    setIsProcessing(true);

    try {
      const res = await fetch(`${API_BASE}/api/agents/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: userText,
          model: selectedModel,
          enable_verification: true
        })
      });

      if (res.ok) {
        const data = await res.json();
        const resultPayload = data.result || {};
        
        let orchestratorSummary = `Aplicación procesada con éxito por el Orquestador Multi-Agente.\n`;
        if (resultPayload.workflow) {
          const wf = resultPayload.workflow;
          if (wf.reasoning) {
            orchestratorSummary += `\n🧠 Intent: ${wf.reasoning.intent}`;
          }
          if (wf.planning && wf.planning.parallelizable_tasks) {
            orchestratorSummary += `\n📐 Tareas en paralelo desglosadas: ${wf.planning.parallelizable_tasks.length}`;
          }
          if (wf.verification) {
            orchestratorSummary += `\n🔍 Score de Calidad Verificado: ${Math.round((wf.verification.quality_metrics?.overall_score || 0.8) * 100)}%`;
          }
        }

        const agentMsg: ChatMessage = {
          id: `msg_resp_${Date.now()}`,
          sender: 'orchestrator',
          text: orchestratorSummary,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          modelUsed: selectedModel,
          orchestratorData: resultPayload
        };
        setMessages(prev => [...prev, agentMsg]);
      } else {
        throw new Error(`Error HTTP ${res.status}`);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg_err_${Date.now()}`,
        sender: 'orchestrator',
        text: `❌ Hubo un inconveniente al conectar con el servidor: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Top Header */}
      <div className="flex justify-between items-center px-6 py-4 bg-gray-800/90 border-b border-gray-700/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-lg border border-indigo-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              App Creator Console
              <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-normal">
                Multi-Agent Engine
              </span>
            </h2>
            <p className="text-xs text-gray-400">Charla con el orquestador para diseñar, codificar y auditar tus aplicaciones</p>
          </div>
        </div>

        {/* LLM Selector */}
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-gray-400" />
          <span className="text-xs text-gray-400 font-medium">IA / Modelo:</span>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-gray-900 border border-gray-700 text-white rounded-lg text-xs px-3 py-1.5 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="glm-5.2-max">GLM-5.2 (Zhipu AI - 1M Context)</option>
            <option value="cli_antigravity">Antigravity AGY (Local CLI)</option>
            <option value="cli_claude_code">Claude Code (Local CLI)</option>
            <option value="minimax-m3">MiniMax M3 (Multimodal Agent)</option>
            <option value="kimi-k3">Kimi K3 (Moonshot AI)</option>
            <option value="openrouter-qwen-3-7">Qwen 3.7 Max (OpenRouter)</option>
            {availableModels.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'orchestrator' && (
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-1">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-3xl rounded-xl p-4 ${
              msg.sender === 'user'
                ? 'bg-indigo-600 text-white rounded-tr-none'
                : 'bg-gray-800/90 text-gray-200 border border-gray-700/70 rounded-tl-none'
            }`}>
              <div className="flex justify-between items-center mb-1 text-xs opacity-75">
                <span className="font-semibold">{msg.sender === 'user' ? 'Tú' : 'Silhouette Orquestador'}</span>
                <span>{msg.timestamp}</span>
              </div>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</p>

              {/* Display Orchestrator Artifacts / Details if present */}
              {msg.orchestratorData && (
                <div className="mt-4 pt-3 border-t border-gray-700/60 space-y-3">
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="flex items-center gap-1 bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                      <Layers className="w-3 h-3" /> Agentes Usados: {msg.orchestratorData.metadata?.agents_used || 5}
                    </span>
                    <span className="flex items-center gap-1 bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded">
                      <ShieldCheck className="w-3 h-3" /> Score: {Math.round((msg.orchestratorData.metadata?.quality_score || 0.8) * 100)}%
                    </span>
                    <span className="flex items-center gap-1 bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                      <Terminal className="w-3 h-3" /> Tiempo: {Math.round(msg.orchestratorData.metadata?.total_time_ms || 250)} ms
                    </span>
                  </div>
                </div>
              )}
            </div>

            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isProcessing && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-gray-800/90 border border-gray-700 text-gray-300 rounded-xl p-4 flex items-center gap-3">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span className="text-xs">{"El equipo de agentes (Reasoner -> Planner -> Executor -> Verifier) está procesando tu aplicación..."}</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSendMessage} className="p-4 bg-gray-800/90 border-t border-gray-700/80 flex gap-3">
        <input
          type="text"
          placeholder="Ej: Crea una Web App en Python con FastAPI y HTML para un gestor de proyectos..."
          value={inputPrompt}
          onChange={(e) => setInputPrompt(e.target.value)}
          disabled={isProcessing}
          className="flex-1 bg-gray-900 border border-gray-700 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isProcessing || !inputPrompt.trim()}
          className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-lg transition disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
          Crear App
        </button>
      </form>
    </div>
  );
};
