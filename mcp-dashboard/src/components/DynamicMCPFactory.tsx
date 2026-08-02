import React, { useState } from 'react';
import { Cpu, Plus, Sparkles, Server, CheckCircle2, Play, RefreshCw, Zap, Shield, Terminal } from 'lucide-react';

interface MCPServerItem {
  id: string;
  name: string;
  transport: 'stdio' | 'sse' | 'http';
  toolsCount: number;
  status: 'active' | 'idle';
  description: string;
}

export const DynamicMCPFactory: React.FC = () => {
  const [servers, setServers] = useState<MCPServerItem[]>([
    {
      id: 'mcp_google_workspace',
      name: 'Google Workspace MCP',
      transport: 'stdio',
      toolsCount: 18,
      status: 'active',
      description: 'Herramientas para Gmail, Google Drive, Calendar, Docs y Sheets.'
    },
    {
      id: 'mcp_microsoft365',
      name: 'Microsoft 365 MCP',
      transport: 'stdio',
      toolsCount: 14,
      status: 'active',
      description: 'Integración con Graph API, Outlook, OneDrive y Teams.'
    },
    {
      id: 'mcp_blender_control',
      name: 'Blender & OS Automation MCP',
      transport: 'sse',
      toolsCount: 6,
      status: 'active',
      description: 'Control de renders 3D en Blender y comandos de sistema.'
    }
  ]);

  const [serverName, setServerName] = useState('');
  const [serverDescription, setServerDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateServer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!serverName.trim() || isCreating) return;

    setIsCreating(true);
    try {
      const res = await fetch('http://localhost:8001/api/mcp/create-server', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: serverName,
          description: serverDescription
        })
      });

      if (res.ok) {
        const data = await res.json();
        const newServer: MCPServerItem = {
          id: data.id || `mcp_${Date.now()}`,
          name: data.name || serverName,
          transport: data.transport || 'sse',
          toolsCount: data.tools_count || 4,
          status: 'active',
          description: data.description || serverDescription || 'Servidor FastMCP activo.'
        };
        setServers(prev => [...prev, newServer]);
        setServerName('');
        setServerDescription('');
      } else {
        throw new Error(`Error HTTP ${res.status}`);
      }
    } catch (err: any) {
      console.error("Error creando servidor MCP:", err.message);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-amber-600/20 text-amber-400 rounded-xl border border-amber-500/30">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              Dynamic FastMCP Factory & Multi-MCP Registry
              <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded-full font-semibold">
                Hot-Reload Protocol
              </span>
            </h2>
            <p className="text-sm text-gray-400">Genera nuevos servidores MCP sobre la marcha y gestiona el registro de herramientas del orquestador</p>
          </div>
        </div>
      </div>

      {/* Creation Card */}
      <form onSubmit={handleCreateServer} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4 shadow-xl">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" /> Crear Nuevo Servidor MCP en Caliente (FastMCP SDK)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Nombre del Servidor (Ej: Blender 3D Renderer MCP)"
            value={serverName}
            onChange={(e) => setServerName(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white rounded-lg p-3 text-sm focus:border-amber-500"
          />
          <input
            type="text"
            placeholder="Descripción de las herramientas que ofrecerá..."
            value={serverDescription}
            onChange={(e) => setServerDescription(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white rounded-lg p-3 text-sm focus:border-amber-500"
          />
        </div>

        <button
          type="submit"
          disabled={isCreating || !serverName.trim()}
          className="flex items-center gap-2 px-6 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg text-sm transition disabled:opacity-50"
        >
          {isCreating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Generar Servidor MCP
        </button>
      </form>

      {/* MCP Registry List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {servers.map((s) => (
          <div key={s.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 shadow-xl relative">
            <div className="flex justify-between items-center border-b border-gray-800 pb-3">
              <h4 className="font-bold text-white text-base flex items-center gap-2">
                <Server className="w-4 h-4 text-amber-400" /> {s.name}
              </h4>
              <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-mono flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {s.status}
              </span>
            </div>

            <p className="text-xs text-gray-400 leading-relaxed">{s.description}</p>

            <div className="flex justify-between items-center text-xs pt-2 text-gray-400 border-t border-gray-800/80 font-mono">
              <span>Transport: {s.transport}</span>
              <span className="text-amber-400 font-bold">{s.toolsCount} Tools Registradas</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
