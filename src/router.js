/**
 * Truss — Hash-based Router
 * Minimal SPA router: hash changes → page render.
 */

const routes = {};
let currentCleanup = null;
let contentEl = null;

export function registerRoute(path, handler) {
  routes[path] = handler;
}

export function navigate(path) {
  window.location.hash = path;
}

export function getCurrentRoute() {
  const hash = window.location.hash.slice(1) || '/';
  return hash;
}

async function handleRoute() {
  const path = getCurrentRoute();
  const handler = routes[path] || routes['/'];

  if (!handler) return;

  // Cleanup previous page
  if (currentCleanup && typeof currentCleanup === 'function') {
    currentCleanup();
    currentCleanup = null;
  }

  if (!contentEl) {
    contentEl = document.getElementById('page-content');
  }
  if (!contentEl) return;

  // Clear content
  contentEl.innerHTML = '';

  // Render new page — handler returns { el, cleanup? }
  const result = await handler();
  if (result.el) {
    contentEl.appendChild(result.el);
  }
  if (result.cleanup) {
    currentCleanup = result.cleanup;
  }

  // Update active nav
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('data-route');
    item.classList.toggle('active', href === path);
  });
}

export function startRouter() {
  window.addEventListener('hashchange', handleRoute);
  // Initial route
  handleRoute();
}

export function destroyRouter() {
  window.removeEventListener('hashchange', handleRoute);
  if (currentCleanup) {
    currentCleanup();
    currentCleanup = null;
  }
}
