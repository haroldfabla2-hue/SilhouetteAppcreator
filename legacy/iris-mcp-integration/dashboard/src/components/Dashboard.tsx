import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { RefreshCw, Activity, Users, TrendingUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import './App.css';

interface AgentMetrics {
  id: string;
  agent: string;
  status: 'active' | 'idle' | 'error';
  tasksCompleted: number;
  avgResponseTime: number;
  tokenUsage: number;
  lastActivity: string;
  successRate: number;
}

interface DashboardProps {
  apiBase: string;
}

const IrisDashboard: React.FC<DashboardProps> = ({ apiBase }) => {
  const [agents, setAgents] = useState<AgentMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [realTimeData, setRealTimeData] = useState<any[]>([]);
  const [totalTokens, setTotalTokens] = useState(0);
  const [totalTasks, setTotalTasks] = useState(0);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`${apiBase}/metrics/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setAgents(data.agents);
        setTotalTokens(data.totalTokens || data.agents.reduce((sum: number, agent: AgentMetrics) => sum + agent.tokenUsage, 0));
        setTotalTasks(data.totalTasks || data.agents.reduce((sum: number, agent: AgentMetrics) => sum + agent.tasksCompleted, 0));
        setRealTimeData(prev => [...prev.slice(-19), {
          timestamp: data.timestamp,
          sales: data.agents[0]?.tasksCompleted || 0,
          support: data.agents[1]?.tasksCompleted || 0,
          consulting: data.agents[2]?.tasksCompleted || 0
        }]);
        setIsConnected(true);
        setLoading(false);
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setLoading(false);
    };

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    return () => {
      eventSource.close();
    };
  }, [apiBase]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const refreshData = async () => {
    setLoading(true);
    // Force refresh by closing and reopening SSE connection
    window.location.reload();
  };

  if (loading && agents.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Cargando dashboard de IRIS...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard IRIS</h1>
            <p className="text-gray-600">Monitoreo de agentes en tiempo real</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
              isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              {isConnected ? 'Conectado' : 'Desconectado'}
            </div>
            <button
              onClick={refreshData}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Actualizar</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Agentes</p>
              <p className="text-3xl font-bold text-gray-900">{agents.length}</p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tareas Completadas</p>
              <p className="text-3xl font-bold text-gray-900">{totalTasks.toLocaleString()}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tokens Procesados</p>
              <p className="text-3xl font-bold text-gray-900">{totalTokens.toLocaleString()}</p>
            </div>
            <Activity className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Promedio Respuesta</p>
              <p className="text-3xl font-bold text-gray-900">
                {agents.length > 0 
                  ? (agents.reduce((sum, agent) => sum + agent.avgResponseTime, 0) / agents.length).toFixed(1)
                  : 0
                }s
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Real Time Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Tareas por Agente (Tiempo Real)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={realTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" tickFormatter={(value) => new Date(value).toLocaleTimeString()} />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleString()}
              />
              <Line type="monotone" dataKey="sales" stroke="#3B82F6" strokeWidth={2} name="Sales Agent" />
              <Line type="monotone" dataKey="support" stroke="#10B981" strokeWidth={2} name="Support Agent" />
              <Line type="monotone" dataKey="consulting" stroke="#F59E0B" strokeWidth={2} name="Consulting Agent" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Performance */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance por Agente</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agents.map(agent => ({
              name: agent.agent,
              tasks: agent.tasksCompleted,
              responseTime: agent.avgResponseTime,
              successRate: agent.successRate * 100
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="tasks" fill="#3B82F6" name="Tareas" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agents Status */}
      <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Estado de Agentes</h2>
        <div className="space-y-4">
          {agents.map((agent) => (
            <div key={agent.id} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-4">
                {getStatusIcon(agent.status)}
                <div>
                  <h3 className="font-medium text-gray-900">{agent.agent}</h3>
                  <p className="text-sm text-gray-600">Última actividad: {new Date(agent.lastActivity).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center space-x-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600">Tareas</p>
                  <p className="text-lg font-semibold">{agent.tasksCompleted}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600">Respuesta</p>
                  <p className="text-lg font-semibold">{agent.avgResponseTime}s</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600">Tokens</p>
                  <p className="text-lg font-semibold">{agent.tokenUsage.toLocaleString()}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600">Éxito</p>
                  <p className="text-lg font-semibold">{(agent.successRate * 100).toFixed(1)}%</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(agent.status)}`}>
                  {agent.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IrisDashboard;