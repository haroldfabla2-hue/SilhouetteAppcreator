import React, { useState, useEffect } from 'react';
import { Command } from 'cmdk';
import { Search, Server, Activity, ArrowRight, X } from 'lucide-react';
// Remove external CSS import since we use Tailwind

interface SearchResult {
  id: string;
  name?: string;
  status?: string;
  app_id?: string;
  type: 'application' | 'agent' | 'task';
}

export const OmniSearchModal = () => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<{ applications: SearchResult[], agents: SearchResult[], active_tasks: SearchResult[] }>({ applications: [], agents: [], active_tasks: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  useEffect(() => {
    if (!query) {
      setResults({ applications: [], agents: [], active_tasks: [] });
      return;
    }
    
    const debounceTimeout = setTimeout(async () => {
      setLoading(true);
      try {
        // En producción llamar a: /api/system/search?query=...
        // Aquí hacemos un mock para el UI
        await new Promise(r => setTimeout(r, 300));
        
        setResults({
          applications: [{ id: "app-1", name: `App de ejemplo para ${query}`, type: 'application' }],
          agents: [{ id: "agent-1", name: `Agent matching ${query}`, type: 'agent' }],
          active_tasks: [{ id: `task-${Date.now()}`, status: "RUNNING", type: 'task' }]
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => clearTimeout(debounceTimeout);
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
        <Command label="Global Search" className="w-full flex flex-col h-full" shouldFilter={false}>
          <div className="flex items-center border-b border-slate-700 px-3 py-2">
            <Search className="w-5 h-5 text-slate-400 mr-2" />
            <Command.Input 
              autoFocus
              placeholder="Search across workspaces, agents, and active tasks (Cmd+K)..." 
              className="flex-1 bg-transparent border-0 outline-none text-slate-100 placeholder:text-slate-500 py-2 focus:ring-0"
              value={query}
              onValueChange={setQuery}
            />
            <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <Command.List className="max-h-[300px] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-slate-400 text-sm">
              {loading ? 'Searching omniverse...' : 'No results found.'}
            </Command.Empty>

            {results.applications.length > 0 && (
              <Command.Group heading="Applications" className="px-2 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {results.applications.map(app => (
                  <Command.Item key={app.id} onSelect={() => setOpen(false)} className="flex items-center px-2 py-3 mt-1 rounded-md cursor-pointer hover:bg-indigo-600/20 aria-selected:bg-indigo-600/20 group">
                    <Server className="w-4 h-4 mr-3 text-indigo-400 group-hover:text-indigo-300" />
                    <span className="text-sm text-slate-200">{app.name}</span>
                    <ArrowRight className="w-4 h-4 ml-auto text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {results.agents.length > 0 && (
              <Command.Group heading="Agents" className="px-2 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">
                {results.agents.map(agent => (
                  <Command.Item key={agent.id} onSelect={() => setOpen(false)} className="flex items-center px-2 py-3 mt-1 rounded-md cursor-pointer hover:bg-blue-600/20 aria-selected:bg-blue-600/20 group">
                    <Activity className="w-4 h-4 mr-3 text-blue-400 group-hover:text-blue-300" />
                    <span className="text-sm text-slate-200">{agent.name}</span>
                    <ArrowRight className="w-4 h-4 ml-auto text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {results.active_tasks.length > 0 && (
              <Command.Group heading="Active Tasks" className="px-2 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mt-2">
                {results.active_tasks.map(task => (
                  <Command.Item key={task.id} onSelect={() => setOpen(false)} className="flex items-center px-2 py-3 mt-1 rounded-md cursor-pointer hover:bg-amber-600/20 aria-selected:bg-amber-600/20 group">
                    <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse mr-4 ml-1"></div>
                    <span className="text-sm font-mono text-slate-300">ID: {task.id}</span>
                    <span className="ml-3 text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded-full">{task.status}</span>
                    <ArrowRight className="w-4 h-4 ml-auto text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Command.Item>
                ))}
              </Command.Group>
            )}
          </Command.List>
          
          <div className="border-t border-slate-700 bg-slate-800/50 p-2 flex justify-between items-center text-xs text-slate-400">
            <span>Powered by SilhouetteMCP</span>
            <div className="flex gap-2">
              <span className="flex items-center"><kbd className="bg-slate-700 rounded px-1.5 py-0.5 mx-1 font-mono">↑</kbd><kbd className="bg-slate-700 rounded px-1.5 py-0.5 mx-1 font-mono">↓</kbd> to navigate</span>
              <span className="flex items-center"><kbd className="bg-slate-700 rounded px-1.5 py-0.5 mx-1 font-mono">enter</kbd> to select</span>
            </div>
          </div>
        </Command>
      </div>
    </div>
  );
};
