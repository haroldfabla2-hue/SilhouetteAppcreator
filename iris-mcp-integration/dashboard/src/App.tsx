import React from 'react';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  return (
    <div className="App">
      <Dashboard apiBase={apiBase} />
    </div>
  );
}

export default App;