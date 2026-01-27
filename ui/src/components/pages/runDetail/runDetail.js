/**
 * Run Detail page component
 * Displays full run record with probe results and evidence
 */

import Handlebars from 'handlebars';
import runDetailTemplate from './runDetail.hbs?raw';
import './runDetail.css';
import runsapi from '@api/runsapi.js';
import messages from '@framework/messages/messages.js';

// Syntax highlighting
import hljs from 'highlight.js';

// Handlebars helpers
Handlebars.registerHelper('eq', (a, b) => a === b);
Handlebars.registerHelper('formatDate', (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });
});
Handlebars.registerHelper('jsonStringify', (obj) => {
  if (!obj) return '';
  return JSON.stringify(obj, null, 2);
});
Handlebars.registerHelper('statusBadgeClass', (status) => {
  const classes = {
    QUEUED: 'badge-queued',
    RUNNING: 'badge-running',
    COMPLETED: 'badge-completed',
    FAILED: 'badge-failed',
  };
  return classes[status] || 'badge-gray';
});
Handlebars.registerHelper('decisionBadgeClass', (verdict) => {
  const classes = {
    ACCEPT: 'badge-accept',
    REVISE: 'badge-revise',
    CONSTRAIN: 'badge-constrain',
    ESCALATE: 'badge-escalate',
  };
  return classes[verdict] || 'badge-gray';
});
Handlebars.registerHelper('verdictBadgeClass', (verdict) => {
  const classes = {
    PASS: 'badge-pass',
    FAIL: 'badge-fail',
    UNCERTAIN: 'badge-uncertain',
    ERROR: 'badge-error',
  };
  return classes[verdict] || 'badge-gray';
});

const template = Handlebars.compile(runDetailTemplate);

const runDetail = {
  appMain: null,
  runId: null,
  runRecord: null,
  loading: false,
  error: null,
  processingMessage: null,
  expandedProbes: new Set(),

  /**
   * Render the page
   */
  async render(params = {}) {
    this.appMain = document.getElementById('app-main');
    this.runId = params.runId;

    if (!this.runId) {
      this.error = 'No run ID provided';
      this._renderTemplate();
      return;
    }

    // Initial render with loading state
    this.loading = true;
    this._renderTemplate();

    try {
      // Fetch run detail
      await this._fetchRunDetail();

      // Check if still processing
      if (this.runRecord && this.runRecord.status === 'RUNNING') {
        this.processingMessage = `Run is still processing... Updated at ${new Date().toLocaleTimeString()}`;
      }

      // Render final content
      this.loading = false;
      this._renderTemplate();

      // Apply syntax highlighting
      this._applySyntaxHighlighting();

      // Bind event listeners
      this._bindEvents();
    } catch (error) {
      this.loading = false;
      this.error = error.message;
      this._renderTemplate();
    }
  },

  /**
   * Fetch run detail from API
   */
  async _fetchRunDetail() {
    try {
      const response = await runsapi.fetchRunDetail(this.runId);

      // Check if still processing (202 response)
      if (response.status === 'RUNNING') {
        this.runRecord = {
          run_id: this.runId,
          status: 'RUNNING',
          message: response.message,
        };
        return;
      }

      this.runRecord = response;
    } catch (error) {
      console.error('Error fetching run detail:', error);
      throw error;
    }
  },

  /**
   * Render template with current state
   */
  _renderTemplate() {
    if (!this.runRecord) {
      const html = template({
        runId: this.runId,
        loading: this.loading,
        error: this.error,
      });
      this.appMain.innerHTML = html;
      return;
    }

    // Extract data from runRecord
    const data = {
      runId: this.runRecord.run_id,
      status: this.runRecord.status,
      createdAt: this.runRecord.created_at,
      updatedAt: this.runRecord.updated_at,
      loading: this.loading,
      error: this.error,
      processingMessage: this.processingMessage,
      decision: this.runRecord.decision || null,
      probeResults: this.runRecord.probe_results || [],
      taskSpec: this.runRecord.task_spec,
      candidateOutput: this.runRecord.candidate_output,
      auditTrace: this.runRecord.audit_trace,
    };

    // Enrich probe results with metadata from probe plan
    if (this.runRecord.probe_plan && this.runRecord.probe_results) {
      data.probeResults = this.runRecord.probe_results.map(result => {
        const probeDef = this.runRecord.probe_plan.probes.find(p => p.probe_id === result.probe_id);
        return {
          ...result,
          description: probeDef?.description || result.probe_id,
          expected_checks: probeDef?.expected_checks || [],
        };
      });
    }

    const html = template(data);
    this.appMain.innerHTML = html;
  },

  /**
   * Apply syntax highlighting to code blocks
   */
  _applySyntaxHighlighting() {
    const codeBlocks = this.appMain.querySelectorAll('.__runDetail-evidence-content code');
    codeBlocks.forEach(block => {
      // Try to detect JSON and highlight
      try {
        hljs.highlightElement(block);
      } catch (e) {
        // Fallback if highlighting fails
        console.warn('Syntax highlighting failed for block:', e);
      }
    });
  },

  /**
   * Bind event listeners
   */
  _bindEvents() {
    // Accordion headers
    const accordionHeaders = this.appMain.querySelectorAll('.__runDetail-accordion-header');
    accordionHeaders.forEach(header => {
      header.addEventListener('click', (e) => this._toggleProbe(e, header));
    });

    // Collapse all button
    const collapseAllBtn = this.appMain.getElementById('btn-collapse-all');
    if (collapseAllBtn) {
      collapseAllBtn.addEventListener('click', () => this._collapseAll());
    }

    // Section toggles
    const sectionToggles = this.appMain.querySelectorAll('.__runDetail-section-toggle');
    sectionToggles.forEach(toggle => {
      toggle.addEventListener('click', (e) => this._toggleSection(e, toggle));
    });

    // Back buttons
    const backRunsBtn = this.appMain.getElementById('btn-back-runs');
    const backBtn = this.appMain.getElementById('btn-back');

    if (backRunsBtn) {
      backRunsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        messages.publish('navigateToRunsList', {});
      });
    }

    if (backBtn) {
      backBtn.addEventListener('click', () => {
        messages.publish('navigateToRunsList', {});
      });
    }

    // Download report button
    const downloadBtn = this.appMain.getElementById('btn-download-report');
    if (downloadBtn) {
      downloadBtn.addEventListener('click', () => this._downloadReport());
    }
  },

  /**
   * Toggle probe accordion
   */
  _toggleProbe(e, header) {
    const item = header.closest('.__runDetail-accordion-item');
    if (!item) return;

    const content = item.querySelector('.__runDetail-accordion-content');
    const icon = header.querySelector('.__runDetail-accordion-icon');
    const probeId = item.getAttribute('data-probe-id');

    const isVisible = content.style.display !== 'none';
    content.style.display = isVisible ? 'none' : 'block';

    if (icon) {
      icon.classList.toggle('rotated');
    }

    // Track expanded state
    if (isVisible) {
      this.expandedProbes.delete(probeId);
    } else {
      this.expandedProbes.add(probeId);
    }
  },

  /**
   * Collapse all probes
   */
  _collapseAll() {
    const items = this.appMain.querySelectorAll('.__runDetail-accordion-item');
    items.forEach(item => {
      const content = item.querySelector('.__runDetail-accordion-content');
      const icon = item.querySelector('.__runDetail-accordion-icon');

      content.style.display = 'none';
      if (icon) {
        icon.classList.remove('rotated');
      }
    });

    this.expandedProbes.clear();
  },

  /**
   * Toggle section visibility
   */
  _toggleSection(e, toggle) {
    e.preventDefault();

    const section = toggle.closest('.__runDetail-section');
    if (!section) return;

    const content = section.querySelector('.__runDetail-section-content');
    const icon = toggle.querySelector('.__runDetail-section-icon');

    const isVisible = content.style.display !== 'none';
    content.style.display = isVisible ? 'none' : 'block';

    if (icon) {
      icon.classList.toggle('rotated');
    }
  },

  /**
   * Download markdown report
   */
  async _downloadReport() {
    try {
      await runsapi.downloadReportMd(this.runId);
    } catch (error) {
      console.error('Error downloading report:', error);
      this.error = `Failed to download report: ${error.message}`;
      this._renderTemplate();
    }
  },

  /**
   * Deactivate page (cleanup)
   */
  deactivate() {
    this.expandedProbes.clear();
  },
};

export default runDetail;
