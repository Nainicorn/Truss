/**
 * Truss — Audit Log Page
 * Filterable table with inline detail expansion.
 */

import { getAudit, getSessions } from '../api/client.js';
import { createBlastBadge } from '../components/blastRadiusBadge.js';

const BASE_URL = import.meta.env.VITE_API_URL || (
  import.meta.env.PROD ? '' : 'http://localhost:8000'
);

export function auditPage() {
  const el = document.createElement('div');
  el.className = 'anim-fade-in stagger-3';

  el.innerHTML = `
    <div class="page-header">
      <span class="page-title">Audit Log</span>
      <span class="page-title-rule"></span>
    </div>

    <div class="filter-row">
      <select id="audit-filter-decision">
        <option value="">All decisions</option>
        <option value="approve">Approve</option>
        <option value="escalate">Escalate</option>
        <option value="block">Block</option>
      </select>
      <select id="audit-filter-session">
        <option value="">All sessions</option>
      </select>
    </div>

    <div id="audit-table-container"></div>
    <div class="pagination" id="audit-pagination"></div>
  `;

  let currentPage = 0;
  const pageSize = 50;
  let expandedId = null;

  async function loadSessions() {
    try {
      const data = await getSessions({ limit: 100 });
      const select = el.querySelector('#audit-filter-session');
      if (!select || !data.sessions) return;
      data.sessions.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = `${s.agent_id || 'unknown'} (${s.id.slice(0, 8)})`;
        select.appendChild(opt);
      });
    } catch (e) {
      // backend offline
    }
  }

  async function loadEntries() {
    const sessionFilter = el.querySelector('#audit-filter-session')?.value || '';
    const container = el.querySelector('#audit-table-container');
    if (!container) return;

    try {
      const data = await getAudit({
        limit: pageSize,
        offset: currentPage * pageSize,
        sessionId: sessionFilter || null,
      });

      if (!data.entries || data.entries.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-title">No audit entries</div>
            <div class="empty-state-text">Gate decisions will appear here once the backend processes requests.</div>
          </div>
        `;
        return;
      }

      await renderTable(container, data.entries, data.total);
    } catch (e) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title">Backend offline</div>
          <div class="empty-state-text">Start the backend: cd backend && uvicorn app.main:app --reload</div>
        </div>
      `;
    }
  }

  async function renderTable(container, entries, total) {
    const decisionFilter = el.querySelector('#audit-filter-decision')?.value || '';

    container.innerHTML = `<div class="empty-state"><div class="empty-state-text">Loading...</div></div>`;

    const details = await Promise.all(entries.map(entry =>
      fetch(`${BASE_URL}/api/audit/${entry.id}`)
        .then(r => r.json())
        .catch(() => null)
    ));

    const rich = details.filter(Boolean).map(d => ({
      ...d.entry,
      request: d.request,
      decision: d.decision,
      signature_valid: d.signature_valid,
    }));

    const displayEntries = decisionFilter
      ? rich.filter(e => e.decision?.decision === decisionFilter)
      : rich;

    if (displayEntries.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title">No matching entries</div>
          <div class="empty-state-text">Try adjusting your filters.</div>
        </div>
      `;
      return;
    }

    const table = document.createElement('table');
    table.className = 'data-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Action</th>
          <th>Decision</th>
          <th>Confidence</th>
          <th>Blast Radius</th>
          <th>Sig</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');
    displayEntries.forEach(entry => {
      const dec = entry.decision;
      const req = entry.request;
      if (!dec || !req) return;

      const layerResults = typeof dec.layer_results === 'string'
        ? JSON.parse(dec.layer_results)
        : (dec.layer_results || {});

      const tr = document.createElement('tr');
      const time = entry.created_at
        ? new Date(entry.created_at).toLocaleTimeString('en-US', { hour12: false })
        : '';

      tr.innerHTML = `
        <td class="col-timestamp">${time}</td>
        <td>${escapeHtml(req.action)}</td>
        <td class="col-decision ${dec.decision}">${dec.decision.toUpperCase()}</td>
        <td>${(dec.confidence ?? 0).toFixed(2)}</td>
        <td class="blast-cell"></td>
        <td style="color: ${entry.signature_valid ? 'var(--approve)' : 'var(--block)'}">${entry.signature_valid ? 'VALID' : 'INVALID'}</td>
      `;

      const blastCell = tr.querySelector('.blast-cell');
      blastCell.innerHTML = '';
      blastCell.appendChild(createBlastBadge(dec.blast_radius));

      tr.addEventListener('click', () => {
        const existing = tbody.querySelector(`.row-detail[data-for="${entry.id}"]`);
        if (existing) {
          existing.remove();
          expandedId = null;
          return;
        }

        tbody.querySelectorAll('.row-detail').forEach(r => r.remove());
        expandedId = entry.id;

        const detailRow = document.createElement('tr');
        detailRow.className = 'row-detail';
        detailRow.setAttribute('data-for', entry.id);
        detailRow.innerHTML = `
          <td colspan="6">
            <div class="detail-grid">
              <div>
                <div class="detail-section-title">Layer 1: Classifier</div>
                <div class="detail-value">
                  Action: ${escapeHtml(layerResults.classifier?.action_key || req.action)}<br>
                  Category: ${escapeHtml(layerResults.classifier?.category || 'unknown')}<br>
                  Reversible: ${dec.reversible ? 'yes' : 'no'}<br>
                  Blast Radius: ${escapeHtml(dec.blast_radius)}
                </div>
              </div>
              <div>
                <div class="detail-section-title">Layer 2: Scanner</div>
                <div class="detail-value">
                  Injection: ${dec.injection_detected ? 'DETECTED' : 'clean'}<br>
                  Pattern: ${escapeHtml(layerResults.scanner?.highest_pattern || 'none')}<br>
                  Confidence: ${(layerResults.scanner?.confidence ?? 0).toFixed(2)}<br>
                  Patterns matched: ${(layerResults.scanner?.matched_patterns || []).length}
                </div>
              </div>
              <div>
                <div class="detail-section-title">Decision</div>
                <div class="detail-value">
                  Verdict: ${dec.decision.toUpperCase()}<br>
                  Reason: ${escapeHtml(dec.reason)}<br>
                  Request ID: ${escapeHtml(entry.request_id?.slice(0, 12) || '')}...
                </div>
              </div>
              <div>
                <div class="detail-section-title">Audit</div>
                <div class="detail-value">
                  Signature: ${escapeHtml(entry.signature?.slice(0, 24) || '')}...<br>
                  Valid: ${entry.signature_valid ? 'yes' : 'NO'}
                </div>
              </div>
            </div>
            ${req.context ? `
              <div style="margin-top: var(--space-md)">
                <div class="detail-section-title">Context</div>
                <div class="detail-value" style="white-space: pre-wrap; max-height: 120px; overflow-y: auto;">${escapeHtml(req.context).slice(0, 500)}</div>
              </div>
            ` : ''}
          </td>
        `;
        tr.after(detailRow);
      });

      tbody.appendChild(tr);
    });

    container.innerHTML = '';
    container.appendChild(table);

    // Pagination
    const pag = el.querySelector('#audit-pagination');
    if (pag) {
      const totalPages = Math.ceil(total / pageSize);
      if (totalPages > 1) {
        pag.innerHTML = `
          <button class="btn" id="audit-prev" ${currentPage === 0 ? 'disabled' : ''}>Prev</button>
          <span>${currentPage + 1} / ${totalPages}</span>
          <button class="btn" id="audit-next" ${currentPage >= totalPages - 1 ? 'disabled' : ''}>Next</button>
        `;
        pag.querySelector('#audit-prev')?.addEventListener('click', () => {
          if (currentPage > 0) { currentPage--; loadEntries(); }
        });
        pag.querySelector('#audit-next')?.addEventListener('click', () => {
          if (currentPage < totalPages - 1) { currentPage++; loadEntries(); }
        });
      } else {
        pag.innerHTML = '';
      }
    }
  }

  // Wire filters
  setTimeout(() => {
    el.querySelector('#audit-filter-decision')?.addEventListener('change', () => {
      currentPage = 0;
      loadEntries();
    });
    el.querySelector('#audit-filter-session')?.addEventListener('change', () => {
      currentPage = 0;
      loadEntries();
    });
  }, 0);

  loadSessions();
  loadEntries();

  return { el };
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}
