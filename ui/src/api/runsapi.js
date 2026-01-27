/**
 * Runs API - Backend communication for evaluation runs
 */

const API_BASE = '/api';

const runsapi = {
  /**
   * Fetch paginated list of runs
   * @param {number} limit - Max number of runs to fetch
   * @param {number} offset - Number of runs to skip
   * @param {string} status - Optional status filter (QUEUED, RUNNING, COMPLETED, FAILED)
   */
  async fetchRuns(limit = 50, offset = 0, status = null) {
    try {
      let url = `${API_BASE}/runs?limit=${limit}&offset=${offset}`;
      if (status) {
        url += `&status=${status}`;
      }

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching runs:', error);
      throw error;
    }
  },

  /**
   * Fetch full run record (includes probe plan, results, decision, trace)
   * @param {string} runId - The run ID
   */
  async fetchRunDetail(runId) {
    try {
      const response = await fetch(`${API_BASE}/runs/${runId}/record`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 202) {
        // Still processing - return partial status
        return {
          run_id: runId,
          status: 'RUNNING',
          message: 'Run is still processing',
        };
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching run detail:', error);
      throw error;
    }
  },

  /**
   * Get quick run status
   * @param {string} runId - The run ID
   */
  async fetchRunStatus(runId) {
    try {
      const response = await fetch(`${API_BASE}/runs/${runId}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching run status:', error);
      throw error;
    }
  },

  /**
   * Fetch audit trace for a run
   * @param {string} runId - The run ID
   */
  async fetchAuditTrace(runId) {
    try {
      const response = await fetch(`${API_BASE}/runs/${runId}/trace`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching audit trace:', error);
      throw error;
    }
  },

  /**
   * Create a new evaluation run
   * @param {object} taskSpec - Task specification
   * @param {object} candidateOutput - Candidate output to evaluate
   * @param {string} idempotencyKey - Optional idempotency key
   */
  async createRun(taskSpec, candidateOutput, idempotencyKey = null) {
    try {
      const headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'dev-key-12345', // Should come from config
      };

      if (idempotencyKey) {
        headers['Idempotency-Key'] = idempotencyKey;
      }

      const response = await fetch(`${API_BASE}/runs`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({
          task_spec: taskSpec,
          candidate_output: candidateOutput,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating run:', error);
      throw error;
    }
  },

  /**
   * Download markdown report for a run
   * @param {string} runId - The run ID
   */
  async downloadReportMd(runId) {
    try {
      const response = await fetch(`${API_BASE}/runs/${runId}/report.md`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Get filename from Content-Disposition header
      const disposition = response.headers.get('Content-Disposition');
      let filename = `polaris-report-${runId}.md`;
      if (disposition && disposition.includes('filename=')) {
        filename = disposition.split('filename=')[1].replace(/"/g, '');
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading report:', error);
      throw error;
    }
  },
};

export default runsapi;
