/**
 * Login component
 * Email-based authentication
 */

import Handlebars from 'handlebars';
import loginTemplate from './login.hbs?raw';
import './login.css';
import usersapi from '@api/usersapi.js';
import messages from '@framework/messages/messages.js';

const template = Handlebars.compile(loginTemplate);

const login = {
  container: null,
  loading: false,
  error: null,

  /**
   * Initialize login component
   * @param {string} containerId - ID of container element
   */
  init(containerId) {
    this.container = document.getElementById(containerId);
    this.render();
    this._bindEvents();
  },

  /**
   * Render login form
   */
  render() {
    const html = template({
      loading: this.loading,
      error: this.error,
    });

    this.container.innerHTML = html;

    // Re-bind events after render
    this._bindEvents();
  },

  /**
   * Bind event listeners
   */
  _bindEvents() {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', (e) => this._handleSubmit(e));

    // Also allow pressing Enter in email field
    const emailInput = document.getElementById('email');
    if (emailInput) {
      emailInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !this.loading) {
          this._handleSubmit(e);
        }
      });
    }
  },

  /**
   * Handle form submission
   */
  async _handleSubmit(e) {
    e.preventDefault();

    const emailInput = document.getElementById('email');
    const email = emailInput.value.trim();

    // Validate email
    if (!this._validateEmail(email)) {
      this.error = 'Please enter a valid email address';
      this.render();
      return;
    }

    // Clear error
    this.error = null;

    // Set loading state
    this.loading = true;
    this.render();

    try {
      // Call login API
      const response = await usersapi.login(email);

      // API sets __punk-userid cookie automatically
      // Publish logged in event so main.js can setup app shell
      this.loading = false;
      messages.publish('loggedIn', { userId: response.user_id || response.id });
    } catch (error) {
      this.loading = false;
      this.error = `Login failed: ${error.message}`;
      this.render();
    }
  },

  /**
   * Validate email format
   */
  _validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },
};

export default login;
