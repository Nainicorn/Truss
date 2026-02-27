/**
 * Truss — App Shell Layout
 * Sidebar + main content area.
 */

import { navigate, getCurrentRoute } from '../router.js';

export function createLayout() {
  const shell = document.createElement('div');
  shell.className = 'app-shell';
  shell.innerHTML = `
    <nav class="sidebar anim-fade-in stagger-1">
      <div class="sidebar-brand">
        <span class="sidebar-brand-icon">&#9650;</span>
        <span class="sidebar-brand-mark">TRUSS</span>
      </div>
      <div class="sidebar-nav">
        <a class="nav-item" data-route="/" href="#/">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="2" width="5" height="5" rx="1"/>
            <rect x="9" y="2" width="5" height="5" rx="1"/>
            <rect x="2" y="9" width="5" height="5" rx="1"/>
            <rect x="9" y="9" width="5" height="5" rx="1"/>
          </svg>
          Dashboard
        </a>
        <a class="nav-item" data-route="/audit" href="#/audit">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/>
            <path d="M5 6h6M5 8.5h6M5 11h3"/>
          </svg>
          Audit Log
        </a>
        <a class="nav-item" data-route="/demo" href="#/demo">
          <svg class="nav-item-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M5 3l8 5-8 5V3z"/>
          </svg>
          Demo
        </a>
      </div>
      <div class="sidebar-status">
        <div class="ws-status disconnected" id="ws-status">
          <span class="ws-dot"></span>
          <span class="ws-status-label">OFFLINE</span>
        </div>
        <div class="sidebar-escalation-count" id="escalation-count"></div>
      </div>
    </nav>
    <main class="main-content anim-fade-in stagger-2">
      <div class="page" id="page-content"></div>
    </main>
  `;

  // Handle nav clicks
  shell.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const route = item.getAttribute('data-route');
      navigate(route);
    });
  });

  // Set active nav on initial render
  const current = getCurrentRoute();
  shell.querySelectorAll('.nav-item').forEach(item => {
    const route = item.getAttribute('data-route');
    item.classList.toggle('active', route === current);
  });

  return shell;
}

export function setWsStatus(connected) {
  const el = document.getElementById('ws-status');
  if (!el) return;
  el.className = `ws-status ${connected ? 'connected' : 'disconnected'}`;
  el.querySelector('.ws-status-label').textContent = connected ? 'LIVE' : 'OFFLINE';
}

export function setEscalationCount(count) {
  const el = document.getElementById('escalation-count');
  if (!el) return;
  el.textContent = count > 0 ? `${count} escalation${count !== 1 ? 's' : ''}` : '';
}
