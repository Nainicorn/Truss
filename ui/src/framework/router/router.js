/**
 * Page router
 * Manages page registration and navigation
 */

const router = {
  pages: {},
  currentPage: null,
  currentParams: {},

  /**
   * Register a page component
   * @param {string} name - Page name
   * @param {object} component - Page component with render() method
   */
  registerPage(name, component) {
    this.pages[name] = component;
  },

  /**
   * Navigate to a page
   * @param {string} pageName - Name of the page to navigate to
   * @param {object} params - Parameters to pass to page.render()
   */
  async goTo(pageName, params = {}) {
    const page = this.pages[pageName];

    if (!page) {
      console.error(`Page '${pageName}' is not registered`);
      return;
    }

    // Deactivate current page if it has a deactivate method
    if (this.currentPage && this.currentPage.deactivate) {
      this.currentPage.deactivate();
    }

    // Update current page state
    this.currentPage = page;
    this.currentParams = params;

    // Render the page
    try {
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
    }
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
