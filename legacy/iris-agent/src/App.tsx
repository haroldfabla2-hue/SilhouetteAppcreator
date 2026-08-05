import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from './stores/appStore';
import Layout from './components/layout/Layout';
import Dashboard from './components/dashboard/Dashboard';
import Chat from './components/chat/Chat';
import Editor from './components/editor/Editor';
import Projects from './components/projects/Projects';
import Canvas from './components/canvas/Canvas';
import Files from './components/files/Files';
import Templates from './components/templates/Templates';
import Settings from './components/settings/Settings';
import Notifications from './components/notifications/Notifications';
import './index.css';

function App() {
  const { theme, activeModal } = useAppStore();

  // Apply theme to document
  React.useEffect(() => {
    if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <Router>
      <div className="min-h-screen bg-background text-foreground">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/editor" element={<Editor />} />
            <Route path="/canvas" element={<Canvas />} />
            <Route path="/files" element={<Files />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>

        {/* Modals */}
        {activeModal === 'notifications' && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="iris-card w-full max-w-2xl m-4 max-h-[80vh] overflow-hidden">
              <Notifications onClose={() => useAppStore.getState().setActiveModal(null)} />
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;