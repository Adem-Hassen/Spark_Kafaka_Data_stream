import React from 'react';
import './ConnectionStatus.css';

const ConnectionStatus = ({ readyState, lastUpdate }) => {
  const connectionStatus = {
    0: { text: 'Connecting...', color: '#f59e0b', icon: '🟡' },
    1: { text: 'Connected', color: '#10b981', icon: '🟢' },
    2: { text: 'Closing', color: '#f59e0b', icon: '🟡' },
    3: { text: 'Disconnected', color: '#ef4444', icon: '🔴' }
  }[readyState];

  return (
    <div className="connection-status">
      <div className="status-bar">
        <div className="status-item">
          <span 
            className="status-dot"
            style={{ backgroundColor: connectionStatus.color }}
          ></span>
          <span>WebSocket: {connectionStatus.text}</span>
        </div>
        
        <div className="status-item">
          <span>📊</span>
          <span>Last Update: {lastUpdate.toLocaleTimeString()}</span>
        </div>
        
        <div className="status-item">
          <span>⚡</span>
          <span>Real-time Spark Processing</span>
        </div>
      </div>
    </div>
  );
};

export default ConnectionStatus;