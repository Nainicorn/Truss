/**
 * Truss — Dashboard Page
 * Live decision feed with summary stats.
 * Full implementation in Step 15.
 */

export function dashboardPage() {
  const el = document.createElement('div');
  el.className = 'anim-fade-in stagger-3';

  el.innerHTML = `
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

    <div id="decision-feed">
      <div class="empty-state">
        <div class="empty-state-title">No decisions yet</div>
        <div class="empty-state-text">Run the demo agent or send a POST /api/gate request to see live decisions.</div>
      </div>
    </div>
  `;

  return { el };
}
