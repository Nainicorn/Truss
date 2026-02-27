/**
 * Truss — Demo Page
 * Side-by-side comparison: agent without Truss vs with Truss.
 * Full implementation in Step 16.
 */

export function demoPage() {
  const el = document.createElement('div');
  el.className = 'anim-fade-in stagger-3';

  el.innerHTML = `
    <div class="page-header">
      <span class="page-title">Demo &mdash; Agent Scenarios</span>
      <span class="page-title-rule"></span>
    </div>

    <div class="filter-row">
      <select id="demo-scenario-select">
        <option value="email_injection">Email Injection</option>
        <option value="file_exfiltration">File Exfiltration</option>
      </select>
      <button class="btn btn-primary" id="demo-run-btn">Run Scenario</button>
    </div>

    <div class="demo-grid">
      <div class="demo-panel">
        <div class="demo-panel-header unsafe">
          Without Truss
        </div>
        <div class="demo-panel-body" id="demo-unsafe-feed">
          <div class="empty-state">
            <div class="empty-state-text">Select a scenario and click Run</div>
          </div>
        </div>
      </div>

      <div class="demo-panel">
        <div class="demo-panel-header safe">
          With Truss
        </div>
        <div class="demo-panel-body" id="demo-safe-feed">
          <div class="empty-state">
            <div class="empty-state-text">Select a scenario and click Run</div>
          </div>
        </div>
      </div>
    </div>
  `;

  return { el };
}
