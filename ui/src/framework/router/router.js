/**
 * Page router
 * Manages page registration and navigation with URL state persistence
 * Uses hash-based routing: #pageName/param1/param2 or #pageName
 */

const router = {
  pages: {},
  currentPage: null,
  currentParams: {},
  isNavigating: false,

  /**
   * Register a page component
   * @param {string} name - Page name
   * @param {object} component - Page component with render() method
   */
  registerPage(name, component) {
    this.pages[name] = component;
  },

  /**
   * Navigate to a page and update URL
   * @param {string} pageName - Name of the page to navigate to
   * @param {object} params - Parameters to pass to page.render()
   */
  async goTo(pageName, params = {}) {
    const page = this.pages[pageName];

    if (!page) {
      console.error(`Page '${pageName}' is not registered`);
      return;
    }

    // Set flag to prevent hashchange from triggering again
    this.isNavigating = true;

    try {
      // Deactivate current page if it has a deactivate method
      if (this.currentPage && this.currentPage.deactivate) {
        this.currentPage.deactivate();
      }

      // Update current page state
      this.currentPage = page;
      this.currentParams = params;

      // Update URL to reflect current state
      this._updateURL(pageName, params);

      // Render the page
      await page.render(params);
    } catch (error) {
      console.error(`Error rendering page '${pageName}':`, error);
      const appMain = document.getElementById('app-main');
      if (appMain) {
        appMain.innerHTML = `
          <div class="error">
            <strong>Error loading page:</strong><br>
            ${error.message}
          </div>
        `;
      }
    } finally {
      // Clear flag after navigation completes
      this.isNavigating = false;
    }
  },

  /**
   * Initialize router and set up URL listeners
   */
  initialize() {
    // Handle back button and URL changes
    window.addEventListener('hashchange', () => {
      // Skip if we're already navigating programmatically (prevents double navigation)
      if (this.isNavigating) return;

      const route = this._parseURL();
      if (route) {
        this.isNavigating = true;
        this.goTo(route.pageName, route.params);
        this.isNavigating = false;
      }
    });
  },

  /**
   * Restore state from URL and navigate if needed
   * Returns true if a route was restored from URL, false if no route found
   */
  restoreFromURL() {
    const route = this._parseURL();
    if (route) {
      this.goTo(route.pageName, route.params);
      return true;
    }
    return false;
  },

  /**
   * Parse URL hash to extract page name and params
   * Format: #pageName/param1/param2
   * @private
   */
  _parseURL() {
    const hash = window.location.hash.slice(1); // Remove #
    if (!hash) return null;

    const parts = hash.split('/');
    const pageName = parts[0];

    if (!this.pages[pageName]) {
      return null;
    }

    // Extract params based on page type
    const params = {};
    if (pageName === 'runDetail' && parts.length > 1) {
      params.runId = parts[1];
    }

    return { pageName, params };
  },

  /**
   * Update URL to reflect current navigation
   * @private
   */
  _updateURL(pageName, params = {}) {
    let hash = pageName;

    if (pageName === 'runDetail' && params.runId) {
      hash = `${pageName}/${params.runId}`;
    }

    window.location.hash = hash;
  },

  /**
   * Get current page name
   */
  getCurrentPageName() {
    return this.currentPage ? Object.keys(this.pages).find(name => this.pages[name] === this.currentPage) : null;
  },

  /**
   * Get current params
   */
  getCurrentParams() {
    return this.currentParams;
  },
};

export default router;
