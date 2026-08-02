import { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Zap, 
  Users, 
  Database, 
  Wifi,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Bot
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { OmniSearchModal } from './OmniSearchModal';

// TypeScript fix for Recharts components
const XAxisComponent = XAxis as any;
const YAxisComponent = YAxis as any;
const TooltipComponent = Tooltip as any;
const LineComponent = Line as any;

interface SystemMetrics {
  timestamp: string;
  cpu: number;
  memory: number;
  agents: number;
  requests: number;
}

interface AgentStatus {
  name: string;
  status: 'active' | 'idle' | 'error';
  tasksCompleted: number;
  lastActivity: string;
  uptime: string;
}

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  source: string;
}

import { ModelManager } from './ModelManager';
import { AppCreatorChat } from './AppCreatorChat';
import { ModelArena } from './ModelArena';
import { DesignInspector } from './DesignInspector';
import { CodeEditor } from './CodeEditor';
import { TerminalManager } from './TerminalManager';
import { DynamicMCPFactory } from './DynamicMCPFactory';
import { Settings, MessageSquare, Swords, Eye, BarChart3, Code, Terminal, Cpu } from 'lucide-react';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat' | 'arena' | 'editor' | 'terminals' | 'mcp' | 'design' | 'settings'>('chat');
  const [metrics, setMetrics] = useState<SystemMetrics[]>([]);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'warning' | 'error'>('healthy');
  const [analyzingError, setAnalyzingError] = useState<string | null>(null);

  const handleAnalyzeError = async (logMessage: string) => {
    setAnalyzingError(logMessage);
    try {
      // Endpoint que acabamos de crear en silhouettemcp_server.py (Fase 2)
      const res = await fetch('http://localhost:8000/api/agents/analyze-error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error_logs: logMessage, context_info: 'Dashboard UI' })
      });
      const data = await res.json();
      alert(`AI Analysis:\n${JSON.stringify(data.analysis, null, 2)}`);
    } catch (err) {
      alert("Failed to reach AI explainer endpoint. Is the server running?");
    } finally {
      setAnalyzingError(null);
    }
  };

  // Simular datos en tiempo real
  useEffect(() => {
    const generateMetrics = (): SystemMetrics => ({
      timestamp: new Date().toLocaleTimeString(),
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      agents: 15 + Math.floor(Math.random() * 20),
      requests: Math.floor(Math.random() * 1000)
    });

    const generateAgents = (): AgentStatus[] => [
      { name: 'Git Operations', status: 'active', tasksCompleted: 127, lastActivity: '30s ago', uptime: '2h 15m' },
      { name: 'Web Scraping', status: 'active', tasksCompleted: 89, lastActivity: '1m ago', uptime: '2h 15m' },
      { name: 'Database Ops', status: 'active', tasksCompleted: 203, lastActivity: '15s ago', uptime: '2h 15m' },
      { name: 'File Processing', status: 'idle', tasksCompleted: 45, lastActivity: '5m ago', uptime: '2h 15m' },
      { name: 'Search Engine', status: 'active', tasksCompleted: 156, lastActivity: '45s ago', uptime: '2h 15m' },
      { name: 'Python Executor', status: 'active', tasksCompleted: 78, lastActivity: '2m ago', uptime: '2h 15m' },
    ];

    const generateLogs = (): LogEntry[] => [
      { timestamp: '14:32:15', level: 'info', message: 'Agent Git Operations completed task #127', source: 'Git Agent' },
      { timestamp: '14:32:10', level: 'info', message: 'Database connection established', source: 'Database Agent' },
      { timestamp: '14:32:05', level: 'warning', message: 'High memory usage detected (78%)', source: 'System Monitor' },
      { timestamp: '14:32:00', level: 'info', message: 'Web scraping task completed successfully', source: 'Web Agent' },
      { timestamp: '14:31:55', level: 'error', message: 'Failed to connect to external API', source: 'Search Agent' },
    ];

    // Cargar datos iniciales
    setMetrics(Array.from({ length: 10 }, (_, i) => generateMetrics()));
    setAgents(generateAgents());
    setLogs(generateLogs());

    // Actualizar métricas cada 2 segundos
    const interval = setInterval(() => {
      setMetrics(prev => [...prev.slice(-9), generateMetrics()]);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-500';
      case 'idle': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />;
      case 'idle': return <Clock className="w-4 h-4" />;
      case 'error': return <AlertTriangle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'info': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <OmniSearchModal />
      {/* Header */}
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">MCP Server Superior Dashboard</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                systemStatus === 'healthy' ? 'bg-green-500' :
                systemStatus === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm font-medium text-gray-600">
                Sistema {systemStatus === 'healthy' ? 'Saludable' : 
                        systemStatus === 'warning' ? 'Con Advertencias' : 'Con Errores'}
              </span>
            </div>
            <span className="text-sm text-gray-500">
              {new Date().toLocaleString('es-ES')}
            </span>
          </div>
        </div>

        {/* Pestañas de Navegación */}
        <div className="flex flex-wrap gap-2 bg-gray-200 p-1.5 rounded-xl">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'chat' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            App Creator (Chat)
          </button>
          <button
            onClick={() => setActiveTab('arena')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'arena' ? 'bg-rose-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Swords className="w-4 h-4" />
            Arena Multi-Modelo
          </button>
          <button
            onClick={() => setActiveTab('editor')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'editor' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Code className="w-4 h-4" />
            Editor de Código
          </button>
          <button
            onClick={() => setActiveTab('terminals')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'terminals' ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Terminal className="w-4 h-4" />
            Consolas Múltiples
          </button>
          <button
            onClick={() => setActiveTab('mcp')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'mcp' ? 'bg-amber-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Cpu className="w-4 h-4" />
            Dynamic FastMCP
          </button>
          <button
            onClick={() => setActiveTab('design')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'design' ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Eye className="w-4 h-4" />
            Design Inspector
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'dashboard' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Métricas & Telemetría
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'settings' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Settings className="w-4 h-4" />
            Configuraciones (Modelos e IA)
          </button>
        </div>
      </div>

      {activeTab === 'chat' ? (
        <AppCreatorChat />
      ) : activeTab === 'arena' ? (
        <ModelArena />
      ) : activeTab === 'editor' ? (
        <CodeEditor />
      ) : activeTab === 'terminals' ? (
        <TerminalManager />
      ) : activeTab === 'mcp' ? (
        <DynamicMCPFactory />
      ) : activeTab === 'design' ? (
        <DesignInspector />
      ) : activeTab === 'settings' ? (
        <ModelManager />
      ) : (
        <>

      {/* Métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Agentes Activos</p>
              <p className="text-2xl font-bold text-gray-900">
                {agents.filter(a => a.status === 'active').length}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-gray-600">
            <TrendingUp className="w-4 h-4 mr-1" />
            <span>{agents.length} total agents</span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CPU Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.length > 0 ? Math.round(metrics[metrics.length - 1].cpu) : 0}%
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Activity className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${metrics.length > 0 ? metrics[metrics.length - 1].cpu : 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Memory Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.length > 0 ? Math.round(metrics[metrics.length - 1].memory) : 0}%
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Database className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${metrics.length > 0 ? metrics[metrics.length - 1].memory : 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Requests/min</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.length > 0 ? metrics[metrics.length - 1].requests : 0}
              </p>
            </div>
            <div className="p-3 bg-orange-100 rounded-full">
              <Wifi className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-gray-600">
            <Zap className="w-4 h-4 mr-1" />
            <span>Rendimiento óptimo</span>
          </div>
        </div>
      </div>

      {/* Gráfico de rendimiento */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Rendimiento del Sistema</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxisComponent dataKey="timestamp" />
              <YAxisComponent />
              <TooltipComponent />
              <LineComponent type="monotone" dataKey="cpu" stroke="#10b981" strokeWidth={2} name="CPU %" />
              <LineComponent type="monotone" dataKey="memory" stroke="#8b5cf6" strokeWidth={2} name="Memory %" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Estado de agentes */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Estado de Agentes</h3>
          <div className="space-y-3">
            {agents.map((agent, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={getStatusColor(agent.status)}>
                    {getStatusIcon(agent.status)}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{agent.name}</p>
                    <p className="text-sm text-gray-600">Last: {agent.lastActivity}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{agent.tasksCompleted}</p>
                  <p className="text-xs text-gray-600">tasks</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Logs en tiempo real */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Logs en Tiempo Real</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">En vivo</span>
          </div>
        </div>
        <div className="bg-black rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
          {logs.map((log, index) => (
            <div key={index} className={`mb-2 p-2 rounded flex justify-between items-start ${getLogLevelColor(log.level)}`}>
              <div>
                <span className="text-gray-400">{log.timestamp}</span>
                <span className="text-gray-300 ml-2">[{log.source}]</span>
                <span className="ml-2">{log.message}</span>
              </div>
              {log.level === 'error' && (
                <button 
                  onClick={() => handleAnalyzeError(log.message)}
                  disabled={analyzingError === log.message}
                  className="ml-4 flex items-center bg-red-600 hover:bg-red-500 text-white px-2 py-1 rounded text-xs transition-colors"
                >
                  <Bot className="w-3 h-3 mr-1" />
                  {analyzingError === log.message ? 'Analyzing...' : 'Ask AI to Fix'}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
      </>
      )}
    </div>
  );
};

export default Dashboard;