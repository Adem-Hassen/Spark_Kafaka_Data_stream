import React, { useState, useEffect, useCallback } from 'react';
import MetricCard from './MetricCard';
import CorrelationMatrix from './CorrelationMatrix';
import PriceChart from './PriceChart';
import ConnectionStatus from './ConnectionStatus';
import { useWebSocket } from '../utils/websocket';
import './Dashboard.css';

const Dashboard = () => {
  const [metrics, setMetrics] = useState([]);
  const [correlations, setCorrelations] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const { lastMessage, readyState } = useWebSocket('ws://localhost:8000/ws/live');

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'initial_data') {
        setMetrics(lastMessage.latest_metrics || []);
        setCorrelations(lastMessage.correlations || []);
      } else if (lastMessage.symbol) {
        // Update individual metric in real-time
        setMetrics(prev => {
          const filtered = prev.filter(m => m.symbol !== lastMessage.symbol);
          return [...filtered, lastMessage];
        });
        setLastUpdate(new Date());
      }
    }
  }, [lastMessage]);

  // Fetch initial data on component mount
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const response = await fetch('http://localhost:8000/metrics/current');
      const data = await response.json();
      setMetrics(data.latest_metrics || []);
      setCorrelations(data.correlations || []);
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
    }
  };

  const handleSymbolSelect = useCallback((symbol) => {
    setSelectedSymbol(selectedSymbol === symbol ? null : symbol);
  }, [selectedSymbol]);

  const filteredMetrics = selectedSymbol 
    ? metrics.filter(m => m.symbol === selectedSymbol)
    : metrics;

  return (
    <div className="dashboard">
      <ConnectionStatus readyState={readyState} lastUpdate={lastUpdate} />
      
      <div className="dashboard-content">
        <div className="metrics-section">
          <h2>Real-time Crypto Metrics</h2>
          <div className="metrics-grid">
            {filteredMetrics.map(metric => (
              <MetricCard 
                key={metric.symbol} 
                metric={metric}
                isSelected={selectedSymbol === metric.symbol}
                onSelect={() => handleSymbolSelect(metric.symbol)}
              />
            ))}
            {filteredMetrics.length === 0 && (
              <div className="no-data">
                <p>📊 Waiting for real-time data...</p>
                <p className="subtext">Spark is processing crypto data from Binance</p>
              </div>
            )}
          </div>
        </div>

        <div className="analytics-section">
          <div className="chart-panel">
            <h3>📈 Price Trends & Analytics</h3>
            <PriceChart 
              metrics={metrics} 
              selectedSymbol={selectedSymbol}
            />
          </div>
          
          <div className="correlation-panel">
            <h3>🔄 Market Correlations</h3>
            <CorrelationMatrix correlations={correlations} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;