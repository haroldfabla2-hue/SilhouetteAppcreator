import React, { useState, useEffect } from 'react';
import { apiService, TaskRequest, TaskResponse, SystemStats } from './services/api';
import './App.css';

function App() {
  const [objetivo, setObjetivo] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const [healthData, statsData] = await Promise.all([
        apiService.healthCheck(),
        apiService.getSystemStats(),
      ]);
      setHealth(healthData);
      setStats(statsData);
    } catch (err: any) {
      console.error('Error cargando información del sistema:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!objetivo.trim()) {
      setError('Por favor ingresa un objetivo');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: TaskRequest = {
        objetivo: objetivo.trim(),
        contexto: {
          timestamp: new Date().toISOString(),
        },
      };

      const response = await apiService.createTask(request);
      setResult(response);
      
      // Recargar estadísticas
      await loadSystemInfo();
    } catch (err: any) {
      setError(err.message || 'Error procesando tarea');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">
            Sistema Multi-Agente Superior
          </h1>
          <p className="text-gray-300">
            Supera a MiniMax Agent con orquestación inteligente de 5 agentes especializados
          </p>
          
          {/* Estado del sistema */}
          {health && (
            <div className="mt-4 flex gap-4 text-sm">
              <span className="px-3 py-1 bg-green-600 rounded-full">
                Estado: {health.status}
              </span>
              <span className="px-3 py-1 bg-blue-600 rounded-full">
                Versión: {health.version}
              </span>
              {health.llm_stats && (
                <span className="px-3 py-1 bg-purple-600 rounded-full">
                  MiniMax M2 gratis: {health.llm_stats.minimax_free_days_remaining} días
                </span>
              )}
            </div>
          )}
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Panel principal */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg shadow-xl p-6">
              <h2 className="text-2xl font-semibold mb-4">Nueva Tarea</h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    ¿Qué quieres lograr?
                  </label>
                  <textarea
                    value={objetivo}
                    onChange={(e) => setObjetivo(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows={4}
                    placeholder="Ejemplo: Analiza las ventajas de usar sistemas multi-agente..."
                    disabled={loading}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !objetivo.trim()}
                  className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-semibold transition-colors"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Procesando con 5 agentes...
                    </span>
                  ) : (
                    'Ejecutar Sistema Multi-Agente'
                  )}
                </button>
              </form>

              {/* Error */}
              {error && (
                <div className="mt-4 p-4 bg-red-900 border border-red-700 rounded-lg">
                  <p className="text-red-200">{error}</p>
                </div>
              )}

              {/* Resultado */}
              {result && (
                <div className="mt-6 space-y-4">
                  <div className="p-4 bg-gray-700 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold">Resultado</h3>
                      <span className={`px-3 py-1 rounded-full text-sm ${
                        result.status === 'completed' ? 'bg-green-600' : 'bg-yellow-600'
                      }`}>
                        {result.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">
                      ID: {result.conversation_id}
                    </p>

                    {result.result && (
                      <div className="space-y-3">
                        {/* Síntesis */}
                        {result.result.synthesis && (
                          <div className="p-3 bg-gray-800 rounded">
                            <h4 className="font-medium mb-2">Síntesis</h4>
                            <p className="text-gray-300 whitespace-pre-wrap">
                              {result.result.synthesis}
                            </p>
                          </div>
                        )}

                        {/* Calidad */}
                        {result.result.quality_score !== undefined && (
                          <div className="p-3 bg-gray-800 rounded">
                            <h4 className="font-medium mb-2">Calidad</h4>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-700 rounded-full h-2">
                                <div
                                  className="bg-green-500 h-2 rounded-full"
                                  style={{ width: `${result.result.quality_score * 100}%` }}
                                />
                              </div>
                              <span className="text-sm">
                                {(result.result.quality_score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Recomendaciones */}
                        {result.result.recommendations && result.result.recommendations.length > 0 && (
                          <div className="p-3 bg-gray-800 rounded">
                            <h4 className="font-medium mb-2">Recomendaciones</h4>
                            <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
                              {result.result.recommendations.map((rec: string, i: number) => (
                                <li key={i}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Metadatos */}
                    {result.metadata && (
                      <div className="mt-3 pt-3 border-t border-gray-600 text-sm text-gray-400">
                        <p>Agentes usados: {result.metadata.agents_used || 'N/A'}</p>
                        <p>Tiempo: {result.metadata.total_time_ms || 0} ms</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Panel de estadísticas */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg shadow-xl p-6">
              <h2 className="text-xl font-semibold mb-4">Estadísticas del Sistema</h2>
              
              {stats ? (
                <div className="space-y-4">
                  {/* LLM Stats */}
                  {stats.llm && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-400 mb-2">LLM Router</h3>
                      <div className="space-y-2 text-sm">
                        <p>Llamadas totales: {stats.llm.total_calls}</p>
                        <p>Días gratis restantes: {stats.llm.minimax_free_days_remaining}</p>
                        
                        {stats.llm.by_provider && (
                          <div className="mt-2 space-y-1">
                            <p className="text-gray-400">Por proveedor:</p>
                            {Object.entries(stats.llm.by_provider).map(([provider, data]: [string, any]) => (
                              <div key={provider} className="pl-3">
                                <p className="capitalize">{provider.replace('_', ' ')}:</p>
                                <p className="text-xs text-gray-500">
                                  {data.calls || 0} llamadas
                                  {data.error_rate !== undefined && ` (${(data.error_rate * 100).toFixed(1)}% errores)`}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Orchestrator Stats */}
                  {stats.orchestrator && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-400 mb-2">Orquestador</h3>
                      <div className="space-y-2 text-sm">
                        <p>Sesiones activas: {stats.orchestrator.active_sessions}</p>
                        <p className="text-gray-400">Agentes:</p>
                        <ul className="pl-3 text-xs text-gray-500 space-y-1">
                          {stats.orchestrator.agents && Object.entries(stats.orchestrator.agents).map(([key, value]) => (
                            <li key={key} className="capitalize">
                              {key}: {Array.isArray(value) ? value.join(', ') : value}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={loadSystemInfo}
                    className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition-colors text-sm"
                  >
                    Actualizar
                  </button>
                </div>
              ) : (
                <p className="text-gray-400">Cargando estadísticas...</p>
              )}
            </div>

            {/* Información */}
            <div className="mt-4 bg-gray-800 rounded-lg shadow-xl p-6">
              <h2 className="text-xl font-semibold mb-4">Agentes</h2>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-2" />
                  <div>
                    <p className="font-medium">Reasoner</p>
                    <p className="text-gray-400 text-xs">Analiza intención y contexto</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2" />
                  <div>
                    <p className="font-medium">Planner</p>
                    <p className="text-gray-400 text-xs">Descompone en subtareas</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mt-2 mr-2" />
                  <div>
                    <p className="font-medium">Executor</p>
                    <p className="text-gray-400 text-xs">Ejecuta herramientas MCP</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-purple-500 rounded-full mt-2 mr-2" />
                  <div>
                    <p className="font-medium">Verifier</p>
                    <p className="text-gray-400 text-xs">Valida calidad</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="w-2 h-2 bg-red-500 rounded-full mt-2 mr-2" />
                  <div>
                    <p className="font-medium">Memory Manager</p>
                    <p className="text-gray-400 text-xs">Gestiona RAG</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
