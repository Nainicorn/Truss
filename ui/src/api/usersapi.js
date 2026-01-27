/**
 * Users API - Backend communication for user authentication
 */

const API_BASE = '/api';

const usersapi = {
  /**
   * Login user with email
   * @param {string} email - User email
   */
  async login(email) {
    try {
      const response = await fetch(`${API_BASE}/users`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Store user ID in cookie (backend sets __punk-userid cookie)
      // Frontend can also access user_id from response if needed
      return data;
    } catch (error) {
      console.error('Error logging in:', error);
      throw error;
    }
  },

  /**
   * Get user profile
   */
  async getProfile() {
    try {
      const response = await fetch(`${API_BASE}/users/profile`, {
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
      console.error('Error fetching profile:', error);
      throw error;
    }
  },

  /**
   * Logout user (clear cookie and session)
   */
  async logout() {
    try {
      const response = await fetch(`${API_BASE}/users/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Logout may fail on backend, but we still clear local state
        console.warn('Backend logout failed, clearing local state');
      }
    } catch (error) {
      console.error('Error logging out:', error);
    }
  },
};

export default usersapi;
