/**
 * Truss — Dashboard Page
 * Live decision feed streamed via WebSocket with summary stats.
 */

import { createDecisionCard } from '../components/decisionCard.js';
import { setWsStatus } from '../components/layout.js';
import { getAudit } from '../api/client.js';

const MAX_VISIBLE = 50;
const FADE_AFTER_MS = 30000;
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function dashboardPage() {
  const el = document.createElement('div');
  el.className = 'anim-fade-in stagger-3';

  el.innerHTML = `
    <div class="radar-bg"></div>
    <div class="page-header">
      <span class="page-title">Live Decisions</span>
      <span class="live-header">
        <span class="live-dot disconnected" id="dashboard-live-dot"></span>
      </span>
      <span class="page-title-rule"></span>
    </div>

    <div class="summary-bar">
      <div class="summary-stat">
        <span class="summary-stat-value approve" id="stat-approved">0</span>
        <span class="summary-stat-label">approved</span>
      </div>
      <div class="summary-stat">
        <span class="summary-stat-value escalate" id="stat-escalated">0</span>
        <span class="summary-stat-label">escalated</span>
      </div>
      <div class="summary-stat">
        <span class="summary-stat-value block" id="stat-blocked">0</span>
        <span class="summary-stat-label">blocked</span>
      </div>
    </div>

    <div class="decision-feed" id="decision-feed"></div>
  `;

  let ws = null;
  let stats = { approve: 0, escalate: 0, block: 0 };
  let fadeTimers = [];

  function updateStats() {
    const a = el.querySelector('#stat-approved');
    const e = el.querySelector('#stat-escalated');
    const b = el.querySelector('#stat-blocked');
    if (a) a.textContent = stats.approve;
    if (e) e.textContent = stats.escalate;
    if (b) b.textContent = stats.block;
  }

  function addDecision(data) {
    const feed = el.querySelector('#decision-feed');
    if (!feed) return;

    // Remove empty state
    const empty = feed.querySelector('.empty-state');
    if (empty) empty.remove();

    // Create card
    const card = createDecisionCard(data);
    feed.insertBefore(card, feed.firstChild);

    // Update stats
    const d = data.decision;
    if (d in stats) stats[d]++;
    updateStats();

    // Trim to max visible
    while (feed.children.length > MAX_VISIBLE) {
      feed.removeChild(feed.lastChild);
    }

    // Fade old cards
    const timer = setTimeout(() => {
      card.style.opacity = '0.4';
      card.style.transition = 'opacity 1s ease';
    }, FADE_AFTER_MS);
    fadeTimers.push(timer);
  }

  function connectWs() {
    const wsUrl = BASE_URL.replace(/^http/, 'ws') + '/ws/decisions';
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsStatus(true);
      const dot = el.querySelector('#dashboard-live-dot');
      if (dot) dot.classList.remove('disconnected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'decision') {
          addDecision(data);
        }
      } catch (e) {
        // ignore malformed
      }
    };

    ws.onclose = () => {
      setWsStatus(false);
      const dot = el.querySelector('#dashboard-live-dot');
      if (dot) dot.classList.add('disconnected');
      // Reconnect after 3s
      setTimeout(() => {
        if (el.isConnected) connectWs();
      }, 3000);
    };

    ws.onerror = () => ws.close();
  }

  // Seed feed with recent decisions from audit API
  async function seedFeed() {
    try {
      const data = await getAudit({ limit: 20 });
      if (!data.entries || data.entries.length === 0) {
        const feed = el.querySelector('#decision-feed');
        if (feed && !feed.querySelector('.decision-card')) {
          feed.innerHTML = `
            <div class="empty-state">
              <div class="empty-state-title">No decisions yet</div>
              <div class="empty-state-text">Run the demo agent or POST to /api/gate to see live decisions.</div>
            </div>
          `;
        }
        return;
      }

      // Fetch full details for each entry
      for (const entry of data.entries.reverse()) {
        try {
          const detail = await (await fetch(`${BASE_URL}/api/audit/${entry.id}`)).json();
          if (detail.request && detail.decision) {
            const req = detail.request;
            const dec = detail.decision;
            addDecision({
              decision: dec.decision,
              action: req.action,
              confidence: dec.confidence,
              blast_radius: dec.blast_radius,
              reversible: dec.reversible,
              injection_detected: dec.injection_detected,
              reason: dec.reason,
              session_id: req.session_id,
              decided_at: dec.decided_at,
              layer_results: typeof dec.layer_results === 'string'
                ? JSON.parse(dec.layer_results)
                : dec.layer_results,
            });
          }
        } catch (e) {
          // skip entries that fail to fetch
        }
      }
    } catch (e) {
      // Backend not running — show empty state
      const feed = el.querySelector('#decision-feed');
      if (feed && !feed.querySelector('.decision-card')) {
        feed.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-title">Backend offline</div>
            <div class="empty-state-text">Start the backend: cd backend && uvicorn app.main:app --reload</div>
          </div>
        `;
      }
    }
  }

  // Start
  seedFeed();
  connectWs();

  function cleanup() {
    if (ws) {
      ws.onclose = null; // prevent reconnect
      ws.close();
    }
    fadeTimers.forEach(clearTimeout);
    setWsStatus(false);
  }

  return { el, cleanup };
}
