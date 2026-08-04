import React, { useState, useEffect } from 'react';
import { Cpu, Server, Plus, Trash2, Download, RefreshCw, CheckCircle2, AlertCircle, Key, Globe, Shield } from 'lucide-react';
import { API_BASE } from "@/lib/api";

interface AIModel {
  id: string;
  name: string;
  provider: string;
  model_name?: string;
  base_url?: string;
  api_key_env?: string;
  context_window?: number;
  is_local?: boolean;
  status?: string;
}

export const ModelManager: React.FC = () => {
  const [cloudModels, setCloudModels] = useState<AIModel[]>([]);
  const [localModels, setLocalModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pullModelName, setPullModelName] = useState<string>('');
  const [pulling, setPulling] = useState<boolean>(false);
  
  // Credentials state
  const [credentials, setCredentials] = useState<Record<string, { is_set: boolean; masked_val: string }>>({});
  const [credForm, setCredForm] = useState({
    openrouter_api_key: '',
    openai_api_key: '',
    zhipu_api_key: '',
    moonshot_api_key: '',
    minimax_api_key: '',
    google_maps_api_key: ''
  });
  const [savingCreds, setSavingCreds] = useState<boolean>(false);

  // Modal / Form state for adding custom model
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [formData, setFormData] = useState({
    name: '',
    provider: 'openai',
    model_name: '',
    base_url: '',
    api_key: '',
    context_window: 128000
  });

  const fetchCredentials = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/system/credentials`);
      if (res.ok) {
        const data = await res.json();
        setCredentials(data.credentials || {});
      }
    } catch (err) {
      console.error('Error fetching credentials:', err);
    }
  };

  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingCreds(true);
    try {
      const res = await fetch(`${API_BASE}/api/system/credentials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credForm)
      });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        fetchCredentials();
        setCredForm({
          openrouter_api_key: '',
          openai_api_key: '',
          zhipu_api_key: '',
          moonshot_api_key: '',
          minimax_api_key: '',
          google_maps_api_key: ''
        });
      } else {
        alert('Error al guardar credenciales');
      }
    } catch (err) {
      alert('Error de conexión con el servidor');
    } finally {
      setSavingCreds(false);
    }
  };

  const fetchModels = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/system/models`);
      if (res.ok) {
        const data = await res.json();
        setCloudModels(data.cloud_and_custom_models || []);
        setLocalModels(data.local_autodiscovered_models || []);
      }
    } catch (err) {
      console.error('Error fetching models:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
    fetchCredentials();
  }, []);

  const handleAddModel = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/system/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setShowAddModal(false);
        setFormData({ name: '', provider: 'openai', model_name: '', base_url: '', api_key: '', context_window: 128000 });
        fetchModels();
      } else {
        alert('Error al registrar modelo');
      }
    } catch (err) {
      alert('Error de conexión');
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (!confirm(`¿Eliminar modelo ${modelId}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/system/models/${modelId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchModels();
      }
    } catch (err) {
      alert('Error al eliminar');
    }
  };

  const handlePullModel = async () => {
    if (!pullModelName) return;
    setPulling(true);
    try {
      const res = await fetch(`${API_BASE}/api/system/local-ai/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: pullModelName })
      });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        setPullModelName('');
        fetchModels();
      } else {
        alert(`Error al descargar: ${data.error}`);
      }
    } catch (err) {
      alert('Error al conectar con Ollama');
    } finally {
      setPulling(false);
    }
  };

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
            <Cpu className="text-indigo-400 w-7 h-7" />
            Configuración de Modelos e Inteligencia Artificial
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Gestión dinámica de modelos Cloud (GLM-5.2, MiniMax, Kimi, OpenRouter) e IAs Locales (Ollama, LM Studio).
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchModels}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition"
          >
            <Plus className="w-4 h-4" />
            Añadir Nueva API / Modelo
          </button>
        </div>
      </div>

      {/* Gestor de Credenciales Globales y Secretos (.env) */}
      <div className="bg-gray-800/80 backdrop-blur border border-gray-700/80 rounded-xl p-5 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-amber-400">
            <Key className="w-5 h-5" />
            Gestor de Credenciales Globales (.env)
          </h2>
          <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1 rounded-full font-medium">
            Seguridad Encriptada
          </span>
        </div>
        <p className="text-xs text-gray-400 mb-4">
          Guarda y aplica tus claves API privadas directamente en el servidor. Los valores actuales se muestran enmascarados.
        </p>

        <form onSubmit={handleSaveCredentials} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              OpenRouter API Key {credentials.OPENROUTER_API_KEY?.is_set && <span className="text-emerald-400">✓</span>}
            </label>
            <input
              type="password"
              placeholder={credentials.OPENROUTER_API_KEY?.masked_val || "sk-or-v1-..."}
              value={credForm.openrouter_api_key}
              onChange={(e) => setCredForm({ ...credForm, openrouter_api_key: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              OpenAI API Key {credentials.OPENAI_API_KEY?.is_set && <span className="text-emerald-400">✓</span>}
            </label>
            <input
              type="password"
              placeholder={credentials.OPENAI_API_KEY?.masked_val || "sk-..."}
              value={credForm.openai_api_key}
              onChange={(e) => setCredForm({ ...credForm, openai_api_key: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Zhipu GLM API Key {credentials.ZHIPU_API_KEY?.is_set && <span className="text-emerald-400">✓</span>}
            </label>
            <input
              type="password"
              placeholder={credentials.ZHIPU_API_KEY?.masked_val || "zhipu-key-..."}
              value={credForm.zhipu_api_key}
              onChange={(e) => setCredForm({ ...credForm, zhipu_api_key: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Moonshot Kimi API Key {credentials.MOONSHOT_API_KEY?.is_set && <span className="text-emerald-400">✓</span>}
            </label>
            <input
              type="password"
              placeholder={credentials.MOONSHOT_API_KEY?.masked_val || "moonshot-key-..."}
              value={credForm.moonshot_api_key}
              onChange={(e) => setCredForm({ ...credForm, moonshot_api_key: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              MiniMax API Key {credentials.MINIMAX_API_KEY?.is_set && <span className="text-emerald-400">✓</span>}
            </label>
            <input
              type="password"
              placeholder={credentials.MINIMAX_API_KEY?.masked_val || "minimax-key-..."}
              value={credForm.minimax_api_key}
              onChange={(e) => setCredForm({ ...credForm, minimax_api_key: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Google Maps API Key {credentials.GOOGLE_MAPS_API_KEY?.is_set && <span className="text-emerald-400">✓</span>}
            </label>
            <input
              type="password"
              placeholder={credentials.GOOGLE_MAPS_API_KEY?.masked_val || "AIzaSy..."}
              value={credForm.google_maps_api_key}
              onChange={(e) => setCredForm({ ...credForm, google_maps_api_key: e.target.value })}
              className="w-full bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="md:col-span-2 lg:col-span-3 flex justify-end pt-2">
            <button
              type="submit"
              disabled={savingCreds}
              className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition disabled:opacity-50"
            >
              {savingCreds ? 'Guardando...' : 'Aplicar y Guardar Credenciales (.env)'}
            </button>
          </div>
        </form>
      </div>

      {/* Local AI Autodiscovery Section */}
      <div className="bg-gray-800/60 backdrop-blur border border-gray-700/60 rounded-xl p-5 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-emerald-400">
            <Server className="w-5 h-5" />
            Servidores de IA Locales Detectados (Ollama :11434 / LM Studio :1234)
          </h2>
          <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Autodescubrimiento Activo
          </span>
        </div>

        {localModels.length === 0 ? (
          <p className="text-sm text-gray-400 italic">No se detectaron servidores locales corriendo en localhost:11434 u 1234.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {localModels.map((m) => (
              <div key={m.id} className="bg-gray-900/80 border border-gray-700 p-4 rounded-lg flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-white">{m.name}</h3>
                  <p className="text-xs text-gray-400">Base URL: {m.base_url}</p>
                </div>
                <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-md font-mono">ONLINE</span>
              </div>
            ))}
          </div>
        )}

        {/* Local Model Downloader */}
        <div className="mt-6 pt-4 border-t border-gray-700/50 flex flex-col md:flex-row gap-3 items-center">
          <div className="flex items-center gap-2 text-sm text-gray-300 font-medium">
            <Download className="w-4 h-4 text-indigo-400" />
            Instalar Modelo Local en Ollama:
          </div>
          <input
            type="text"
            placeholder="Ej: llama3:70b, deepseek-coder, qwen:14b..."
            value={pullModelName}
            onChange={(e) => setPullModelName(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-700 text-white rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={handlePullModel}
            disabled={pulling || !pullModelName}
            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
          >
            {pulling ? 'Descargando...' : 'Instalar Modelo'}
          </button>
        </div>
      </div>

      {/* Cloud & Custom Registered Models */}
      <h2 className="text-lg font-semibold flex items-center gap-2 text-white mb-4">
        <Globe className="w-5 h-5 text-indigo-400" />
        Modelos Registrados (Cloud & APIs Personalizadas)
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {cloudModels.map((m) => (
          <div key={m.id} className="bg-gray-800/80 border border-gray-700/80 rounded-xl p-5 flex flex-col justify-between hover:border-gray-600 transition">
            <div>
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-white text-base">{m.name}</h3>
                <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded font-mono uppercase">
                  {m.provider}
                </span>
              </div>
              <p className="text-xs text-gray-400 font-mono mb-2">ID: {m.id}</p>
              {m.base_url && <p className="text-xs text-gray-400 truncate">URL: {m.base_url}</p>}
              {m.context_window && (
                <p className="text-xs text-gray-400 mt-1">Contexto: {(m.context_window / 1000).toFixed(0)}k tokens</p>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-gray-700/50 flex justify-between items-center">
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5" />
                Listo para Usar
              </span>
              <button
                onClick={() => handleDeleteModel(m.id)}
                className="text-gray-400 hover:text-red-400 p-1 transition"
                title="Eliminar modelo"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Añadir Modelo */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-4">Añadir Nueva API / Modelo de IA</h2>
            <form onSubmit={handleAddModel} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Nombre Visible</label>
                <input
                  type="text"
                  required
                  placeholder="Ej: GLM-5.2 Prod, Custom vLLM, DeepSeek V4..."
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Proveedor / Adaptador</label>
                  <select
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="openai">OpenAI / Compatible</option>
                    <option value="openrouter">OpenRouter</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="zhipu">Zhipu (GLM)</option>
                    <option value="moonshot">Moonshot (Kimi)</option>
                    <option value="minimax">MiniMax</option>
                    <option value="ollama">Ollama Local</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Model Name (API String)</label>
                  <input
                    type="text"
                    placeholder="Ej: glm-5.2, kimi-k3, gpt-4o..."
                    value={formData.model_name}
                    onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Base URL (Opcional)</label>
                <input
                  type="text"
                  placeholder="Ej: https://api.z.ai/api/paas/v4 o http://localhost:11434"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">API Key (Encriptada)</label>
                <input
                  type="password"
                  placeholder="sk-..."
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition"
                >
                  Guardar Modelo
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
