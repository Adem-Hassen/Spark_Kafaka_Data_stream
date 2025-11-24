import React from 'react';
import './MetricCard.css';

const MetricCard = ({ metric, isSelected, onSelect }) => {
  if (!metric) return null;

  const {
    symbol,
    current_price,
    moving_avg_1min,
    price_volatility,
    price_trend,
    price_change,
    high_1min,
    low_1min,
    trade_count
  } = metric;

  const trendConfig = {
    up: { icon: '📈', color: '#10b981', bgColor: '#ecfdf5' },
    down: { icon: '📉', color: '#ef4444', bgColor: '#fef2f2' },
    stable: { icon: '➡️', color: '#6b7280', bgColor: '#f9fafb' }
  };

  const config = trendConfig[price_trend] || trendConfig.stable;

  return (
    <div 
      className={`metric-card ${isSelected ? 'selected' : ''}`}
      style={{ 
        borderLeft: `4px solid ${config.color}`,
        backgroundColor: isSelected ? config.bgColor : 'white'
      }}
      onClick={onSelect}
    >
      <div className="card-header">
        <h3 className="symbol">{symbol.replace('USDT', '')}</h3>
        <span className="trend-indicator" style={{ color: config.color }}>
          {config.icon} {price_trend}
        </span>
      </div>

      <div className="price-section">
        <div className="current-price">${current_price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</div>
        <div 
          className="price-change" 
          style={{ color: price_change >= 0 ? '#10b981' : '#ef4444' }}
        >
          {price_change >= 0 ? '+' : ''}{price_change?.toFixed(2)}%
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-item">
          <span className="label">Moving Avg:</span>
          <span className="value">${moving_avg_1min?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
        </div>
        <div className="metric-item">
          <span className="label">Volatility:</span>
          <span className="value">{price_volatility?.toFixed(6)}</span>
        </div>
        <div className="metric-item">
          <span className="label">24h High:</span>
          <span className="value">${high_1min?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
        </div>
        <div className="metric-item">
          <span className="label">24h Low:</span>
          <span className="value">${low_1min?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
        </div>
        <div className="metric-item">
          <span className="label">Trades:</span>
          <span className="value">{trade_count?.toLocaleString()}</span>
        </div>
      </div>

      <div className="card-footer">
        <small>Live from Binance</small>
      </div>
    </div>
  );
};

export default MetricCard;