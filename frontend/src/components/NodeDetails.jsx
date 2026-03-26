import React from 'react';

function NodeDetails({ node, onClose }) {
  if (!node) return null;

  return (
    <div className="node-details">
      <div className="node-details-header">
        <h3>{node.label || node.id}</h3>
        <button className="node-details-close" onClick={onClose}>✕</button>
      </div>
      <div className="node-details-type">{node.type}</div>
      <div className="node-details-props">
        <div className="node-prop">
          <span className="node-prop-key">Node ID</span>
          <span className="node-prop-value">{node.id}</span>
        </div>
        {node.data && Object.entries(node.data).map(([key, value]) => (
          <div key={key} className="node-prop">
            <span className="node-prop-key">{key.replace(/_/g, ' ')}</span>
            <span className="node-prop-value">{value || '—'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NodeDetails;