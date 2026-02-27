/**
 * Truss — Injection Alert Component
 * Displays injection detection details with highlighted context.
 */

export function createInjectionAlert(decision) {
  const el = document.createElement('div');
  el.className = 'injection-alert';

  const layerResults = decision.layer_results || {};
  const scanner = layerResults.scanner || {};
  const patternName = scanner.pattern || 'unknown';
  const confidence = (scanner.confidence ?? decision.confidence ?? 0).toFixed(2);
  const context = decision.context || '';

  el.innerHTML = `
    <div class="injection-alert-header">Injection Detected</div>
    <div class="injection-alert-pattern">
      Pattern: ${escapeHtml(patternName)} &nbsp;(confidence: ${confidence})
    </div>
    ${context ? `<div class="injection-alert-excerpt">${truncateContext(escapeHtml(context), 200)}</div>` : ''}
  `;

  return el;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function truncateContext(text, maxLen) {
  if (text.length <= maxLen) return `"${text}"`;
  return `"${text.slice(0, maxLen)}…"`;
}
