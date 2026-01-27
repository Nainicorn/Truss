/**
 * Runs List page component
 * Displays paginated list of evaluation runs with filters
 */

import Handlebars from 'handlebars';
import runsTemplate from './runsList.hbs?raw';
import './runsList.css';
import runsapi from '@api/runsapi.js';
import messages from '@framework/messages/messages.js';

// Handlebars helpers
Handlebars.registerHelper('eq', (a, b) => a === b);
Handlebars.registerHelper('formatDate', (date) => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });
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

const template = Handlebars.compile(runsTemplate);

const runsList = {
  appMain: null,
  runs: [],
  total: 0,
  loading: false,
  error: null,
  limit: 50,
  offset: 0,
  filterMinId: '',
  statusFilter: '',
  pollingInterval: null,
  hasActiveRuns: false,

  /**
   * Render the page
   */
  async render(params = {}) {
    this.appMain = document.getElementById('app-main');

    // Initial render with loading state
    this.loading = true;
    this._renderTemplate();

    try {
      // Fetch runs
      await this._fetchRuns();

      // Render final content
      this.loading = false;
      this._renderTemplate();

      // Bind event listeners
      this._bindEvents();

      // Start polling if there are active runs
      this._startPolling();
    } catch (error) {
      this.loading = false;
      this.error = error.message;
      this._renderTemplate();
    }
  },

  /**
   * Fetch runs from API
   */
  async _fetchRuns() {
    try {
      const response = await runsapi.fetchRuns(this.limit, this.offset, this.statusFilter || null);

      this.runs = response.runs || [];
      this.total = response.total || 0;

      // Check if there are any active runs
      this.hasActiveRuns = this.runs.some(r => r.status === 'QUEUED' || r.status === 'RUNNING');

      // Calculate stats
      this._calculateStats();
    } catch (error) {
      console.error('Error fetching runs:', error);
      throw error;
    }
  },

  /**
   * Calculate summary stats
   */
  _calculateStats() {
    const stats = {
      passRate: 0,
      decisionBreakdown: {
        ACCEPT: 0,
        REVISE: 0,
        CONSTRAIN: 0,
        ESCALATE: 0,
      },
    };

    let completedWithDecision = 0;

    this.runs.forEach(run => {
      if (run.run_record && run.run_record.decision) {
        completedWithDecision++;
        const verdict = run.run_record.decision.verdict;
        if (stats.decisionBreakdown[verdict] !== undefined) {
          stats.decisionBreakdown[verdict]++;
        }
      }
    });

    if (completedWithDecision > 0) {
      stats.passRate = Math.round((stats.decisionBreakdown.ACCEPT / completedWithDecision) * 100);
    }

    this.passRate = stats.passRate;
    this.decisionBreakdown = stats.decisionBreakdown;
  },

  /**
   * Render template with current state
   */
  _renderTemplate() {
    const currentPage = Math.floor(this.offset / this.limit) + 1;
    const totalPages = Math.ceil(this.total / this.limit);

    const html = template({
      runs: this.runs,
      total: this.total,
      loading: this.loading,
      error: this.error,
      filterMinId: this.filterMinId,
      statusFilter: this.statusFilter,
      passRate: this.passRate || 0,
      decisionBreakdown: this.decisionBreakdown,
      currentPage,
      totalPages,
      isPreviousDisabled: this.offset === 0,
      isNextDisabled: this.offset + this.limit >= this.total,
    });

    this.appMain.innerHTML = html;
  },

  /**
   * Bind event listeners
   */
  _bindEvents() {
    // Table row clicks
    const rows = document.querySelectorAll('.__runsList-row');
    rows.forEach(row => {
      row.addEventListener('click', (e) => {
        const runId = row.getAttribute('data-run-id');
        messages.publish('navigateToRun', { runId });
      });
    });

    // Pagination
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this._previousPage());
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => this._nextPage());
    }

    // Refresh button
    const refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this._refreshRuns());
    }

    // Filters with debounce
    const minIdInput = document.getElementById('filter-min-id');
    if (minIdInput) {
      minIdInput.addEventListener('input', (e) => {
        this.filterMinId = e.target.value;
        clearTimeout(this.filterDebounceTimer);
        this.filterDebounceTimer = setTimeout(() => {
          this.offset = 0;
          this.render();
        }, 300);
      });
    }

    const statusSelect = document.getElementById('filter-status');
    if (statusSelect) {
      statusSelect.addEventListener('change', (e) => {
        this.statusFilter = e.target.value;
        this.offset = 0;
        this.render();
      });
    }

    // Evolution summary toggle
    const summaryToggle = document.getElementById('btn-toggle-summary');
    const summaryContent = document.getElementById('summary-content');

    if (summaryToggle && summaryContent) {
      summaryToggle.addEventListener('click', () => {
        const isVisible = summaryContent.style.display !== 'none';
        summaryContent.style.display = isVisible ? 'none' : 'block';

        const icon = summaryToggle.querySelector('.__runsList-summary-icon');
        if (icon) {
          icon.classList.toggle('rotated');
        }
      });
    }
  },

  /**
   * Previous page
   */
  _previousPage() {
    if (this.offset > 0) {
      this.offset -= this.limit;
      this.render();
    }
  },

  /**
   * Next page
   */
  _nextPage() {
    if (this.offset + this.limit < this.total) {
      this.offset += this.limit;
      this.render();
    }
  },

  /**
   * Refresh runs
   */
  async _refreshRuns() {
    try {
      this.loading = true;
      this._renderTemplate();
      await this._fetchRuns();
      this.loading = false;
      this._renderTemplate();
      this._bindEvents();
    } catch (error) {
      this.error = error.message;
      this.loading = false;
      this._renderTemplate();
    }
  },

  /**
   * Start polling for active runs
   */
  _startPolling() {
    // Clear existing polling
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }

    // Only poll if there are active runs
    if (!this.hasActiveRuns) {
      return;
    }

    // Poll every 3 seconds while there are active runs
    this.pollingInterval = setInterval(async () => {
      try {
        await this._fetchRuns();
        this._renderTemplate();
        this._bindEvents();

        // Stop polling if no more active runs
        if (!this.hasActiveRuns) {
          clearInterval(this.pollingInterval);
        }
      } catch (error) {
        console.error('Error polling for updates:', error);
      }
    }, 3000);
  },

  /**
   * Deactivate page (cleanup)
   */
  deactivate() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }

    if (this.filterDebounceTimer) {
      clearTimeout(this.filterDebounceTimer);
    }
  },
};

export default runsList;
