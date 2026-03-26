const API_BASE = import.meta.env.VITE_API_URL || '';

export async function sendChatMessage(message) {
  const response = await fetch(`${API_BASE}/api/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
}

export async function getGraphData(limit = 200) {
  const response = await fetch(`${API_BASE}/api/graph/?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch graph data');
  return response.json();
}

export async function getNodeNeighbors(nodeId, depth = 1) {
  const response = await fetch(`${API_BASE}/api/graph/node/${encodeURIComponent(nodeId)}?depth=${depth}`);
  if (!response.ok) throw new Error('Failed to fetch node data');
  return response.json();
}

export async function searchNodes(query) {
  const response = await fetch(`${API_BASE}/api/graph/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) throw new Error('Failed to search nodes');
  return response.json();
}

export async function getGraphStats() {
  const response = await fetch(`${API_BASE}/api/graph/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

export async function getNodeTypes() {
  const response = await fetch(`${API_BASE}/api/graph/types`);
  if (!response.ok) throw new Error('Failed to fetch node types');
  return response.json();
}

export async function clearChatHistory() {
  const response = await fetch(`${API_BASE}/api/chat/clear`, { method: 'POST' });
  return response.json();
}