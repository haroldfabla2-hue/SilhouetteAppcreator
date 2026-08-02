import React, { useState } from 'react';
import { Eye, MousePointer, Layout, Palette, Code, CheckCircle, Sparkles, Copy, Terminal } from 'lucide-react';

export const DesignInspector: React.FC = () => {
  const [selectedElement, setSelectedElement] = useState<string>('Header Component (.header-main)');
  const [primaryColor, setPrimaryColor] = useState<string>('#4f46e5');
  const [themeMode, setThemeMode] = useState<'dark' | 'glassmorphism' | 'cyberpunk'>('glassmorphism');

  const simulatedCSS = `
/* CSS Computado de ${selectedElement} */
.${selectedElement.toLowerCase().replace(/[^a-z0-9]/g, '-')}-box {
  background: ${themeMode === 'glassmorphism' ? 'rgba(255, 255, 255, 0.05)' : '#0f172a'};
  backdrop-filter: blur(12px);
  border: 1px solid ${primaryColor}40;
  border-radius: 12px;
  color: #ffffff;
  padding: 1.5rem;
  box-shadow: 0 10px 25px -5px ${primaryColor}20;
}
  `.trim();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-600/20 text-purple-400 rounded-xl border border-purple-500/30">
            <Eye className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              Visual Design Inspector (Mode Orca UI)
              <span className="text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-0.5 rounded-full font-semibold">
                Live DOM & Theme Tuner
              </span>
            </h2>
            <p className="text-sm text-gray-400">Inspecciona elementos visuales en vivo, ajusta tokens CSS y genera prompts de refinamiento de UI</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Live Element Selector & Config */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-5 shadow-xl">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <MousePointer className="w-4 h-4 text-purple-400" />
            Selector de Componentes DOM
          </h3>

          <div className="space-y-2">
            <label className="text-xs text-gray-400 uppercase font-semibold">Elemento Seleccionado</label>
            <select
              value={selectedElement}
              onChange={(e) => setSelectedElement(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-2.5 text-sm font-medium"
            >
              <option value="Header Component (.header-main)">Header Component (.header-main)</option>
              <option value="Navigation Bar (.nav-items)">Navigation Bar (.nav-items)</option>
              <option value="Hero Action Card (.hero-card)">Hero Action Card (.hero-card)</option>
              <option value="Data Grid Table (.data-table)">Data Grid Table (.data-table)</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs text-gray-400 uppercase font-semibold">Estilo de Diseño (Aesthetics)</label>
            <div className="grid grid-cols-3 gap-2">
              {(['dark', 'glassmorphism', 'cyberpunk'] as const).map(mode => (
                <button
                  key={mode}
                  onClick={() => setThemeMode(mode)}
                  className={`py-2 px-3 rounded-lg text-xs font-semibold capitalize transition ${
                    themeMode === mode ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs text-gray-400 uppercase font-semibold">Color Primario Acabado</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="w-10 h-10 rounded-lg bg-transparent cursor-pointer border-0"
              />
              <span className="text-sm font-mono text-gray-300">{primaryColor}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Live Visual Canvas & CSS Inspector */}
        <div className="lg:col-span-2 space-y-6">
          {/* Visual Canvas Preview */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl space-y-4">
            <h3 className="font-bold text-white text-base flex items-center gap-2">
              <Layout className="w-4 h-4 text-purple-400" />
              Previsualización de Componente en Vivo
            </h3>

            <div className="p-8 rounded-xl border border-gray-800 flex items-center justify-center min-h-[160px] transition-all" style={{
              background: themeMode === 'glassmorphism'
                ? 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%)'
                : themeMode === 'cyberpunk'
                ? '#090d16'
                : '#0f172a',
              backdropFilter: 'blur(16px)',
              borderColor: `${primaryColor}40`
            }}>
              <div className="text-center space-y-2">
                <div className="inline-block p-3 rounded-xl mb-2" style={{ backgroundColor: `${primaryColor}20`, color: primaryColor }}>
                  <Sparkles className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-white">{selectedElement}</h4>
                <p className="text-xs text-gray-400">Estilo renderizado dinámicamente usando tokens del Design System</p>
              </div>
            </div>
          </div>

          {/* Computed CSS Code Box */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-xl space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                <Code className="w-4 h-4 text-purple-400" />
                CSS Computado & Tokens Extraídos
              </h4>
              <button
                onClick={() => navigator.clipboard.writeText(simulatedCSS)}
                className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 font-semibold"
              >
                <Copy className="w-3.5 h-3.5" /> Copiar CSS
              </button>
            </div>
            <pre className="bg-gray-950 p-4 rounded-lg text-xs font-mono text-purple-300 overflow-x-auto border border-gray-800">
              <code>{simulatedCSS}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
