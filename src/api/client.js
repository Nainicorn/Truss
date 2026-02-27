/**
 * Truss — API Client
 * Fetch wrapper for the backend.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function health() {
  return request('/api/health');
}

export async function gate(action, params = {}, context = '', sessionId = null) {
  const body = { action, params, context };
  if (sessionId) body.session_id = sessionId;
  return request('/api/gate', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function getAudit({ limit = 50, offset = 0, sessionId = null } = {}) {
  let path = `/api/audit?limit=${limit}&offset=${offset}`;
  if (sessionId) path += `&session_id=${sessionId}`;
  return request(path);
}

export async function getAuditEntry(id) {
  return request(`/api/audit/${id}`);
}

export async function getSessions({ limit = 50, offset = 0 } = {}) {
  return request(`/api/sessions?limit=${limit}&offset=${offset}`);
}

export async function getSession(id) {
  return request(`/api/sessions/${id}`);
}

export async function createSession(agentId, metadata = {}) {
  return request('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId, metadata }),
  });
}

/**
 * WebSocket connection for real-time escalation events.
 */
export function connectEscalations(onMessage, onOpen, onClose) {
  const wsUrl = BASE_URL.replace(/^http/, 'ws') + '/ws/escalations';
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    if (onOpen) onOpen();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (e) {
      // ignore malformed messages
    }
  };

  ws.onclose = () => {
    if (onClose) onClose();
  };

  ws.onerror = () => {
    ws.close();
  };

  return ws;
}
