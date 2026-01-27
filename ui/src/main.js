/**
 * Main entry point for Polaris UI
 * Handles: app shell, router initialization, navigation
 */

import './style.css';
import messages from '@framework/messages/messages.js';
import router from '@framework/router/router.js';
import runsList from '@components/pages/runsList/runsList.js';
import runDetail from '@components/pages/runDetail/runDetail.js';

/**
 * Get or create app container elements
 */
function setupAppShell() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="app-shell">
      <header class="app-header">
        <div class="app-header-title">
          <div class="app-header-logo"><i class="fa-solid fa-asterisk"></i></div>
          <span>Polaris</span>
        </div>
      </header>
      <main class="app-main" id="app-main"></main>
    </div>
  `;
}

/**
 * Initialize router and register all pages
 */
function initializeRouter() {
  const appMain = document.getElementById('app-main');

  router.registerPage('runsList', runsList);
  router.registerPage('runDetail', runDetail);

  // Store reference to appMain container in each page
  runsList.appMain = appMain;
  runDetail.appMain = appMain;
}

/**
 * Setup event listeners for navigation
 */
function setupEventListeners() {
  // Navigate to run detail
  messages.subscribe('navigateToRun', (msg, data) => {
    router.goTo('runDetail', data);
  });

  // Navigate back to runs list
  messages.subscribe('navigateToRunsList', (msg, data) => {
    router.goTo('runsList', data);
  });
}

/**
 * Initialize app on page load
 */
function initializeApp() {
  setupEventListeners();
  setupAppShell();
  initializeRouter();

  // Initialize router with URL listeners
  router.initialize();

  // Try to restore previous route from URL
  const restored = router.restoreFromURL();

  // If no route in URL, default to runsList
  if (!restored) {
    router.goTo('runsList');
  }
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
