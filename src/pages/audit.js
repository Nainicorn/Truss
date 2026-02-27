/**
 * Truss — Audit Log Page
 * Filterable table of all gate decisions with inline detail expansion.
 * Full implementation in Step 17.
 */

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

    <div id="audit-table-container">
      <div class="empty-state">
        <div class="empty-state-title">No audit entries</div>
        <div class="empty-state-text">Gate decisions will appear here once the backend is running.</div>
      </div>
    </div>
  `;

  return { el };
}
