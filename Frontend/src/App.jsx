import React from 'react';
import Dashboard from './components/Dashboard.jsx';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🚀 Crypto Spark Dashboard</h1>
          <p>Real-time cryptocurrency metrics powered by Apache Spark & Kafka</p>
        </div>
      </header>
      <Dashboard />
    </div>
  );
}

export default App;