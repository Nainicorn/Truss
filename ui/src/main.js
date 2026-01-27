/**
 * Main entry point for Polaris UI
 * Handles: auth, app shell, router initialization, navigation
 */

import './style.css';
import messages from '@framework/messages/messages.js';
import router from '@framework/router/router.js';
import login from '@components/login/login.js';
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
          <div class="app-header-logo">⚡</div>
          <span>Polaris</span>
        </div>
        <div class="app-header-actions">
          <button class="btn btn-secondary btn-sm" id="btn-logout">Logout</button>
        </div>
      </header>
      <main class="app-main" id="app-main"></main>
    </div>
  `;

  // Attach logout handler
  document.getElementById('btn-logout').addEventListener('click', () => {
    logout();
  });
}

/**
 * Check if user is authenticated (has __punk-userid cookie)
 */
function isAuthenticated() {
  const cookies = document.cookie.split(';');
  return cookies.some(cookie => cookie.trim().startsWith('__punk-userid='));
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

  // Login event - setup app shell and show runs list
  messages.subscribe('loggedIn', (msg, data) => {
    setupAppShell();
    initializeRouter();
    router.goTo('runsList');
  });

  // Logout event
  messages.subscribe('logout', (msg, data) => {
    document.getElementById('app').innerHTML = '';
    showLoginPage();
  });
}

/**
 * Show login page
 */
function showLoginPage() {
  const app = document.getElementById('app');
  app.innerHTML = '<div id="login-container"></div>';
  login.init('login-container');
}

/**
 * Logout user - clear cookie and show login
 */
function logout() {
  // Clear the cookie
  document.cookie = '__punk-userid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';

  // Publish logout event
  messages.publish('logout', {});
}

/**
 * Initialize app on page load
 */
function initializeApp() {
  setupEventListeners();

  if (isAuthenticated()) {
    // User is logged in - show app shell and runs list
    setupAppShell();
    initializeRouter();
    router.goTo('runsList');
  } else {
    // Not logged in - show login page
    showLoginPage();
  }
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
