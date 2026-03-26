import React, { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape from 'cytoscape';
import { getGraphData, searchNodes, getNodeNeighbors } from '../services/api';
import NodeDetails from './NodeDetails';

const NODE_COLORS = {
  sales_order_headers: '#6366f1',
  sales_order_items: '#818cf8',
  sales_order_schedule_lines: '#a5b4fc',
  outbound_delivery_headers: '#22c55e',
  outbound_delivery_items: '#4ade80',
  billing_document_headers: '#f59e0b',
  billing_document_items: '#fbbf24',
  billing_document_cancellations: '#ef4444',
  business_partners: '#3b82f6',
  business_partner_addresses: '#60a5fa',
  customer_company_assignments: '#2563eb',
  customer_sales_area_assignments: '#1d4ed8',
  products: '#8b5cf6',
  product_descriptions: '#a78bfa',
  product_plants: '#7c3aed',
  product_storage_locations: '#6d28d9',
  plants: '#14b8a6',
  payments_accounts_receivable: '#ec4899',
  journal_entry_items_accounts_receivable: '#f97316',
};

function getNodeColor(type) {
  return NODE_COLORS[type] || '#64748b';
}

function GraphVisualization({ highlightedNodes }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [graphStats, setGraphStats] = useState({ nodes: 0, edges: 0 });
  const [nodeTypes, setNodeTypes] = useState([]);
  const [nodeLimit, setNodeLimit] = useState(150);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, []);

  const buildCytoscape = useCallback((graphData) => {
    if (!containerRef.current || !mountedRef.current) return;

    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    const elements = [];
    const seenNodes = new Set();

    for (const node of graphData.nodes || []) {
      if (seenNodes.has(node.id)) continue;
      seenNodes.add(node.id);
      elements.push({
        group: 'nodes',
        data: {
          id: node.id,
          label: (node.label || node.id).substring(0, 25),
          type: node.type,
          fullData: JSON.stringify(node.data || {}),
          bgColor: getNodeColor(node.type),
        },
      });
    }

    for (const edge of graphData.edges || []) {
      if (seenNodes.has(edge.source) && seenNodes.has(edge.target)) {
        elements.push({
          group: 'edges',
          data: {
            id: `e_${edge.source}_${edge.target}_${Math.random().toString(36).substr(2,5)}`,
            source: edge.source,
            target: edge.target,
            label: edge.relationship || '',
          },
        });
      }
    }

    if (!containerRef.current || !mountedRef.current) return;

    try {
      const cy = cytoscape({
        container: containerRef.current,
        elements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': 'data(bgColor)',
              'label': 'data(label)',
              'color': '#f1f5f9',
              'text-valign': 'bottom',
              'text-halign': 'center',
              'font-size': '8px',
              'font-family': 'Inter, sans-serif',
              'text-margin-y': 5,
              'width': 22,
              'height': 22,
              'border-width': 1.5,
              'border-color': '#ffffff',
              'border-opacity': 0.4,
              'text-max-width': '70px',
              'text-wrap': 'ellipsis',
              'text-outline-color': '#0f172a',
              'text-outline-width': 2,
              'min-zoomed-font-size': 4,
            },
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 3,
              'border-color': '#ffffff',
              'border-opacity': 1,
              'width': 30,
              'height': 30,
            },
          },
          {
            selector: 'node.highlighted',
            style: {
              'border-width': 4,
              'border-color': '#fbbf24',
              'border-opacity': 1,
              'width': 34,
              'height': 34,
              'z-index': 999,
              'background-color': '#fbbf24',
            },
          },
          {
            selector: 'edge',
            style: {
              'width': 1,
              'line-color': '#475569',
              'target-arrow-color': '#475569',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'arrow-scale': 0.5,
              'opacity': 0.4,
            },
          },
        ],
        layout: {
          name: 'cose',
          animate: false,
          nodeOverlap: 20,
          idealEdgeLength: 60,
          nodeRepulsion: function() { return 8000; },
          gravity: 0.5,
          numIter: 200,
          padding: 30,
          randomize: true,
        },
        minZoom: 0.05,
        maxZoom: 4,
      });

      cy.on('tap', 'node', (evt) => {
        const nd = evt.target.data();
        let parsedData = {};
        try { parsedData = JSON.parse(nd.fullData || '{}'); } catch(e) {}
        setSelectedNode({
          id: nd.id,
          label: nd.label,
          type: nd.type,
          data: parsedData,
        });
      });

      cy.on('tap', (evt) => {
        if (evt.target === cy) setSelectedNode(null);
      });

      cy.on('dbltap', 'node', async (evt) => {
        try {
          const neighborData = await getNodeNeighbors(evt.target.id(), 1);
          if (!cyRef.current) return;
          const existing = new Set(cyRef.current.nodes().map(n => n.id()));
          for (const node of neighborData.nodes || []) {
            if (!existing.has(node.id)) {
              cyRef.current.add({
                group: 'nodes',
                data: {
                  id: node.id,
                  label: (node.label || node.id).substring(0, 25),
                  type: node.type,
                  fullData: JSON.stringify(node.data || {}),
                  bgColor: getNodeColor(node.type),
                },
              });
              existing.add(node.id);
            }
          }
          for (const edge of neighborData.edges || []) {
            if (existing.has(edge.source) && existing.has(edge.target)) {
              const eid = `e_${edge.source}_${edge.target}_${Math.random().toString(36).substr(2,5)}`;
              cyRef.current.add({
                group: 'edges',
                data: { id: eid, source: edge.source, target: edge.target },
              });
            }
          }
          cyRef.current.layout({ name: 'cose', animate: true, animationDuration: 500 }).run();
        } catch (e) { console.error(e); }
      });

      cyRef.current = cy;

      const types = new Set();
      for (const n of graphData.nodes || []) if (n.type) types.add(n.type);
      setNodeTypes(Array.from(types));
      setGraphStats({ nodes: graphData.nodes?.length || 0, edges: graphData.edges?.length || 0 });

    } catch (err) {
      console.error('Cytoscape init error:', err);
    }
  }, []);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getGraphData(nodeLimit);
      if (mountedRef.current) buildCytoscape(data);
    } catch (e) {
      console.error('Failed to load graph:', e);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [nodeLimit, buildCytoscape]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  useEffect(() => {
    if (!cyRef.current || !highlightedNodes || !highlightedNodes.length) return;
    const cy = cyRef.current;
    cy.nodes().removeClass('highlighted');
    for (const nid of highlightedNodes) {
      cy.nodes().forEach((n) => {
        const searchable = (n.id() + ' ' + (n.data('label') || '') + ' ' + (n.data('fullData') || '')).toLowerCase();
        if (searchable.includes(nid.toLowerCase())) {
          n.addClass('highlighted');
        }
      });
    }
    const hl = cy.nodes('.highlighted');
    if (hl.length > 0) cy.fit(hl, 50);
  }, [highlightedNodes]);

  const handleSearch = () => {
    if (!searchQuery.trim() || !cyRef.current) return;
    const cy = cyRef.current;
    cy.nodes().removeClass('highlighted');
    const q = searchQuery.toLowerCase();
    cy.nodes().forEach((n) => {
      const searchable = (n.id() + ' ' + (n.data('label') || '') + ' ' + (n.data('fullData') || '')).toLowerCase();
      if (searchable.includes(q)) n.addClass('highlighted');
    });
    const hl = cy.nodes('.highlighted');
    if (hl.length > 0) cy.fit(hl, 50);
  };

  const handleReset = () => {
    if (cyRef.current) {
      cyRef.current.nodes().removeClass('highlighted');
      cyRef.current.fit();
    }
    setSelectedNode(null);
  };

    return (
    <div className="graph-panel">
      <div className="graph-toolbar">
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch}>Search</button>
        <button onClick={handleReset}>Reset</button>
        <button onClick={loadGraph}>Reload</button>
        <select
          value={nodeLimit}
          onChange={(e) => setNodeLimit(Number(e.target.value))}
          style={{
            padding: '6px 8px', borderRadius: '6px',
            border: '1px solid var(--border)',
            background: 'var(--bg-card)', color: 'var(--text-primary)',
            fontSize: '12px',
          }}
        >
          <option value={100}>100 nodes</option>
          <option value={300}>300 nodes</option>
          <option value={500}>500 nodes</option>
          <option value={1000}>1000 nodes</option>
          <option value={2000}>2000 nodes</option>
        </select>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {graphStats.nodes}n · {graphStats.edges}e · Dbl-click expand
        </span>
      </div>

      <div className="graph-container">
        <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
        {loading && (
          <div style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%,-50%)', zIndex: 5,
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
            color: 'var(--text-secondary)'
          }}>
            <div className="spinner" />
            <span>Loading graph...</span>
          </div>
        )}
      </div>

      {nodeTypes.length > 0 && (
        <div className="graph-legend">
          {nodeTypes.slice(0, 8).map((type) => (
            <div key={type} className="legend-item">
              <div className="legend-color" style={{ backgroundColor: getNodeColor(type) }} />
              <span>{type.replace(/_/g, ' ')}</span>
            </div>
          ))}
          {nodeTypes.length > 8 && <span style={{ color: 'var(--text-muted)' }}>+{nodeTypes.length - 8} more</span>}
        </div>
      )}

      {selectedNode && (
        <NodeDetails node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
}

export default GraphVisualization;