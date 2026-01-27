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
  return classes[status] || '';
});
Handlebars.registerHelper('decisionBadgeClass', (verdict) => {
  const classes = {
    ACCEPT: 'badge-accept',
    REVISE: 'badge-revise',
    CONSTRAIN: 'badge-constrain',
    ESCALATE: 'badge-escalate',
  };
  return classes[verdict] || '';
});

const template = Handlebars.compile(runsTemplate);

const runsList = {
  appMain: null,
  runs: [],
  total: 0,
  loading: false,
  loadingMore: false,
  error: null,
  limit: 50,
  offset: 0,
  pollingInterval: null,
  autoRefreshInterval: null,
  hasActiveRuns: false,
  intersectionObserver: null,

  /**
   * Render the page
   */
  async render(params = {}) {
    this.appMain = document.getElementById('app-main');

    // Initial render with loading state
    this.loading = true;
    this.runs = []; // Reset runs for new filters
    this.offset = 0; // Reset offset for new filters
    this._renderTemplate();

    try {
      // Fetch first batch of runs
      await this._fetchRuns();

      // Render final content
      this.loading = false;
      this._renderTemplate();

      // Bind event listeners and setup infinite scroll
      this._bindEvents();
      this._setupInfiniteScroll();

      // Start auto-refresh
      this._setupAutoRefresh();

      // Start polling if there are active runs
      this._startPolling();
    } catch (error) {
      this.loading = false;
      this.error = error.message;
      this._renderTemplate();
    }
  },

  /**
   * Fetch runs from API (append to existing list for infinite scroll)
   */
  async _fetchRuns() {
    try {
      const response = await runsapi.fetchRuns(this.limit, this.offset, null);

      const newRuns = response.runs || [];
      this.total = response.total || 0;

      // Append new runs to existing list (only for infinite scroll)
      this.runs = this.runs.concat(newRuns);

      // Check if there are any active runs
      this.hasActiveRuns = this.runs.some(r => r.status === 'QUEUED' || r.status === 'RUNNING');
    } catch (error) {
      console.error('Error fetching runs:', error);
      throw error;
    }
  },

  /**
   * Fetch and replace runs from offset 0 (for polling and refresh)
   */
  async _refreshRunsFromTop() {
    try {
      const response = await runsapi.fetchRuns(this.limit, 0, null);

      const newRuns = response.runs || [];
      this.total = response.total || 0;

      // Replace the entire list with fresh data from top
      this.runs = newRuns;

      // Check if there are any active runs
      this.hasActiveRuns = newRuns.some(r => r.status === 'QUEUED' || r.status === 'RUNNING');
    } catch (error) {
      console.error('Error refreshing runs:', error);
      throw error;
    }
  },

  /**
   * Render template with current state
   */
  _renderTemplate() {
    const html = template({
      runs: this.runs,
      total: this.total,
      loading: this.loading,
      error: this.error,
    });

    this.appMain.innerHTML = html;
  },

  /**
   * Update loading indicator for infinite scroll
   */
  _updateLoadingMore(show) {
    const loadingMore = document.getElementById('loading-more');
    if (loadingMore) {
      loadingMore.style.display = show ? 'flex' : 'none';
    }
    this.loadingMore = show;
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

    // Create run button
    const createBtn = document.getElementById('btn-create-run');
    if (createBtn) {
      createBtn.addEventListener('click', () => this._openCreateRunModal());
    }

    // Modal close button
    const closeBtn = document.getElementById('btn-close-modal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this._closeCreateRunModal());
    }

    // Modal cancel button
    const cancelBtn = document.getElementById('btn-cancel-form');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this._closeCreateRunModal());
    }

    // Form submission
    const form = document.getElementById('create-run-form');
    if (form) {
      form.addEventListener('submit', (e) => this._handleCreateRunSubmit(e));
    }

    // Close modal when clicking outside
    const modal = document.getElementById('create-run-modal');
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this._closeCreateRunModal();
        }
      });
    }
  },

  /**
   * Open create run modal
   */
  _openCreateRunModal() {
    const modal = document.getElementById('create-run-modal');
    if (modal) {
      modal.style.display = 'flex';
      // Focus on first input
      const firstInput = modal.querySelector('input');
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
      }
    }
  },

  /**
   * Close create run modal
   */
  _closeCreateRunModal() {
    const modal = document.getElementById('create-run-modal');
    if (modal) {
      modal.style.display = 'none';
    }
    // Reset form
    const form = document.getElementById('create-run-form');
    if (form) {
      form.reset();
    }
  },

  /**
   * Handle create run form submission
   */
  async _handleCreateRunSubmit(e) {
    e.preventDefault();

    const form = document.getElementById('create-run-form');
    const submitBtn = document.getElementById('btn-submit-form');

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating...';

      // Parse form data
      const formData = new FormData(form);

      // Build task spec
      const constraints = formData.get('constraints')
        .split('\n')
        .map(c => c.trim())
        .filter(c => c.length > 0);

      const allowedTools = formData.get('allowed_tools')
        .split('\n')
        .map(t => t.trim())
        .filter(t => t.length > 0);

      const domainTags = formData.get('domain_tags')
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);

      const taskSpec = {
        task_id: formData.get('task_id'),
        description: formData.get('description'),
        constraints: constraints.length > 0 ? constraints : [],
        allowed_tools: allowedTools.length > 0 ? allowedTools : null,
        domain_tags: domainTags.length > 0 ? domainTags : [],
        rubric_id: formData.get('rubric_id') || null,
      };

      // Build candidate output
      const candidateOutput = {
        candidate_id: formData.get('candidate_id'),
        content: formData.get('content'),
        metadata: {},
      };

      // Create run via API
      const response = await runsapi.createRun(taskSpec, candidateOutput);

      // Close modal
      this._closeCreateRunModal();

      // Refresh runs from top (replaces entire list to avoid duplicates)
      await this._refreshRunsFromTop();
      this._renderTemplate();
      this._bindEvents();
      this._setupInfiniteScroll();
      this._startPolling();

      // Show success message
      console.log('Run created:', response);
    } catch (error) {
      console.error('Error creating run:', error);
      alert(`Failed to create run: ${error.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Run';
    }
  },

  /**
   * Setup auto-refresh every 30 seconds
   */
  _setupAutoRefresh() {
    // Clear existing interval if any
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
    }

    // Auto-refresh every 30 seconds
    this.autoRefreshInterval = setInterval(async () => {
      try {
        await this._autoRefreshRuns();
      } catch (error) {
        console.error('Error in auto-refresh:', error);
      }
    }, 30000); // 30 seconds
  },

  /**
   * Auto-refresh runs without showing loading state
   */
  async _autoRefreshRuns() {
    try {
      const response = await runsapi.fetchRuns(this.limit, 0, null);
      const newRuns = response.runs || [];
      const newTotal = response.total || 0;

      // Check if there are any active runs
      this.hasActiveRuns = newRuns.some(r => r.status === 'QUEUED' || r.status === 'RUNNING');

      // Only update if data has changed (compare first batch)
      if (JSON.stringify(newRuns) !== JSON.stringify(this.runs.slice(0, newRuns.length))) {
        // Replace first page with fresh data, keep remaining loaded pages
        this.runs = newRuns.concat(this.runs.slice(newRuns.length));
        this.total = newTotal;
        this._renderTemplate();
        this._bindEvents();
      }
    } catch (error) {
      console.error('Error auto-refreshing runs:', error);
    }
  },

  /**
   * Setup Intersection Observer for infinite scroll
   */
  _setupInfiniteScroll() {
    const sentinel = document.getElementById('scroll-sentinel');
    if (!sentinel) return;

    // Clean up old observer if exists
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }

    // Create new observer
    this.intersectionObserver = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          // When sentinel is visible and we haven't loaded all runs
          if (entry.isIntersecting && !this.loadingMore && this.runs.length < this.total) {
            this._loadMoreRuns();
          }
        });
      },
      { threshold: 0.1 }
    );

    this.intersectionObserver.observe(sentinel);
  },

  /**
   * Load more runs on infinite scroll
   */
  async _loadMoreRuns() {
    // Don't load if already at the end
    if (this.runs.length >= this.total) {
      return;
    }

    this._updateLoadingMore(true);

    try {
      this.offset = this.runs.length; // Set offset to current count
      await this._fetchRuns();
      this._renderTemplate();
      this._bindEvents();
      this._setupInfiniteScroll();
    } catch (error) {
      console.error('Error loading more runs:', error);
      this.error = `Failed to load more runs: ${error.message}`;
    } finally {
      this._updateLoadingMore(false);
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
        // Refresh from top to avoid appending duplicates
        await this._refreshRunsFromTop();
        this._renderTemplate();
        this._bindEvents();

        // Stop polling if no more active runs
        if (!this.hasActiveRuns) {
          clearInterval(this.pollingInterval);
          this.pollingInterval = null;
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

    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
      this.autoRefreshInterval = null;
    }

    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
      this.intersectionObserver = null;
    }
  },
};

export default runsList;
