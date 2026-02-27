/**
 * Truss — Decision Card Component
 * Renders a single gate decision.
 */

import { createBlastBadge } from './blastRadiusBadge.js';
import { createInjectionAlert } from './injectionAlert.js';

export function createDecisionCard(decision) {
  const card = document.createElement('div');
  card.className = 'decision-card';
  card.setAttribute('data-decision', decision.decision);

  const d = decision;
  const time = d.decided_at
    ? new Date(d.decided_at).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';

  card.innerHTML = `
    <div class="decision-card-header">
      <span class="decision-verdict ${d.decision}">${d.decision.toUpperCase()}</span>
      <span class="decision-confidence">${(d.confidence ?? 0).toFixed(2)}</span>
    </div>
    <div class="decision-action">${escapeHtml(d.action || '')}</div>
    <div class="decision-meta">
      ${d.session_id ? `<span>Session: ${d.session_id.slice(0, 8)}</span>` : ''}
      ${time ? `<span>${time}</span>` : ''}
    </div>
  `;

  // Blast badge in header
  const header = card.querySelector('.decision-card-header');
  const badge = createBlastBadge(d.blast_radius || 'none');
  header.insertBefore(badge, header.querySelector('.decision-confidence'));

  // Injection alert if detected
  if (d.injection_detected) {
    const body = document.createElement('div');
    body.className = 'decision-card-body';
    const alert = createInjectionAlert(d);
    body.appendChild(alert);
    card.appendChild(body);
  }

  return card;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
