import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './PriceChart.css';

const PriceChart = ({ metrics, selectedSymbol }) => {
  // Transform metrics for charting
  const chartData = metrics.map(metric => ({
    symbol: metric.symbol.replace('USDT', ''),
    price: metric.current_price,
    movingAvg: metric.moving_avg_1min,
    volatility: metric.price_volatility * 1000, // Scale for visibility
    trend: metric.price_trend
  }));

  const filteredData = selectedSymbol 
    ? chartData.filter(d => d.symbol === selectedSymbol.replace('USDT', ''))
    : chartData.slice(0, 8); // Show top 8 if none selected

  if (filteredData.length === 0) {
    return (
      <div className="price-chart">
        <div className="no-data">
          <p>📈 Waiting for price data...</p>
          <p className="subtext">Select a cryptocurrency to view detailed charts</p>
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="label">{`${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.name}: ${typeof entry.value === 'number' 
                ? entry.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })
                : entry.value
              }`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="price-chart">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={filteredData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="symbol" 
            angle={-45}
            textAnchor="end"
            height={60}
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6" 
            strokeWidth={3}
            name="Current Price"
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: '#1d4ed8' }}
          />
          <Line 
            type="monotone" 
            dataKey="movingAvg" 
            stroke="#10b981" 
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Moving Average"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="chart-info">
        <p className="info-text">
          {selectedSymbol 
            ? `Showing real-time data for ${selectedSymbol.replace('USDT', '')}`
            : 'Showing top cryptocurrencies (click any card to filter)'
          }
        </p>
      </div>
    </div>
  );
};

export default PriceChart;