import React, { useState, useEffect } from 'react';
import GraphVisualization from './components/GraphVisualization';
import ChatInterface from './components/ChatInterface';
import { getGraphStats } from './services/api';
import './App.css';

function App() {
  const [highlightedNodes, setHighlightedNodes] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getGraphStats().then(setStats).catch(console.error);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <div className="app-header">
        <h1>
          <span className="icon">🔗</span>
          Graph Query System
        </h1>
        <div className="header-stats">
          {stats && (
            <>
              <div className="stat">
                Nodes: <span className="stat-value">{stats.total_nodes}</span>
              </div>
              <div className="stat">
                Edges: <span className="stat-value">{stats.total_edges}</span>
              </div>
              <div className="stat">
                Types: <span className="stat-value">{Object.keys(stats.node_types || {}).length}</span>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="main-content">
        <GraphVisualization highlightedNodes={highlightedNodes} />
        <ChatInterface onHighlightNodes={setHighlightedNodes} />
      </div>
    </div>
  );
}

export default App;