import React from 'react';
import './CorrelationMatrix.css';

const CorrelationMatrix = ({ correlations }) => {
  if (!correlations || correlations.length === 0) {
    return (
      <div className="correlation-matrix">
        <div className="no-data">
          <p>🔄 Loading correlation data...</p>
          <p className="subtext">Real-time correlations will appear here</p>
        </div>
      </div>
    );
  }

  // Extract unique symbols and create correlation map
  const symbols = [...new Set(correlations.flatMap(corr => corr.pair.split('-')))];
  const correlationMap = {};
  
  correlations.forEach(corr => {
    const [sym1, sym2] = corr.pair.split('-');
    correlationMap[`${sym1}-${sym2}`] = corr.correlation;
    correlationMap[`${sym2}-${sym1}`] = corr.correlation;
  });

  const getCorrelationColor = (value) => {
    const intensity = Math.min(Math.abs(value) * 2, 1);
    if (value > 0) {
      return `rgba(34, 197, 94, ${intensity})`;
    } else if (value < 0) {
      return `rgba(239, 68, 68, ${intensity})`;
    }
    return 'rgba(156, 163, 175, 0.2)';
  };

  const getCorrelationText = (value) => {
    if (value > 0.7) return 'Strong Positive';
    if (value > 0.3) return 'Positive';
    if (value > -0.3) return 'Neutral';
    if (value > -0.7) return 'Negative';
    return 'Strong Negative';
  };

  return (
    <div className="correlation-matrix">
      <div className="matrix-container">
        <table>
          <thead>
            <tr>
              <th className="corner"></th>
              {symbols.map(symbol => (
                <th key={symbol} className="symbol-header">
                  {symbol.replace('USDT', '')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {symbols.map(sym1 => (
              <tr key={sym1}>
                <td className="symbol-header row-header">
                  {sym1.replace('USDT', '')}
                </td>
                {symbols.map(sym2 => {
                  if (sym1 === sym2) {
                    return (
                      <td key={sym2} className="diagonal">
                        <div className="correlation-cell">1.00</div>
                      </td>
                    );
                  }
                  
                  const correlation = correlationMap[`${sym1}-${sym2}`] || 0;
                  
                  return (
                    <td key={sym2}>
                      <div 
                        className="correlation-cell"
                        style={{ 
                          backgroundColor: getCorrelationColor(correlation),
                          color: Math.abs(correlation) > 0.5 ? 'white' : 'black'
                        }}
                        title={`${getCorrelationText(correlation)}: ${correlation.toFixed(2)}`}
                      >
                        {correlation.toFixed(2)}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="correlation-legend">
        <div className="legend-item">
          <span className="color-box" style={{backgroundColor: 'rgba(239, 68, 68, 0.8)'}}></span>
          <span>Negative</span>
        </div>
        <div className="legend-item">
          <span className="color-box" style={{backgroundColor: 'rgba(156, 163, 175, 0.2)'}}></span>
          <span>Neutral</span>
        </div>
        <div className="legend-item">
          <span className="color-box" style={{backgroundColor: 'rgba(34, 197, 94, 0.8)'}}></span>
          <span>Positive</span>
        </div>
      </div>
    </div>
  );
};

export default CorrelationMatrix;