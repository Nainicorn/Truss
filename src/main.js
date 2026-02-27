/**
 * Truss — Entry Point
 * Boots the app shell, registers routes, starts the router.
 */

import './styles/base.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/animations.css';

import { createLayout } from './components/layout.js';
import { registerRoute, startRouter } from './router.js';
import { dashboardPage } from './pages/dashboard.js';
import { auditPage } from './pages/audit.js';
import { demoPage } from './pages/demo.js';

// Mount app shell
const app = document.getElementById('app');
app.appendChild(createLayout());

// Register routes
registerRoute('/', dashboardPage);
registerRoute('/audit', auditPage);
registerRoute('/demo', demoPage);

// Start
startRouter();
