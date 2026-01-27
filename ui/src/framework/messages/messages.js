/**
 * Event bus / Pub-Sub messaging system
 * Enables loose coupling between components and pages
 */

const messages = {
  subscribers: {},

  /**
   * Subscribe to a message topic
   * @param {string} topic - The topic to subscribe to
   * @param {function} callback - Called with (topic, data) when message is published
   * @returns {function} Unsubscribe function
   */
  subscribe(topic, callback) {
    if (!this.subscribers[topic]) {
      this.subscribers[topic] = [];
    }

    this.subscribers[topic].push(callback);

    // Return unsubscribe function
    return () => {
      const index = this.subscribers[topic].indexOf(callback);
      if (index > -1) {
        this.subscribers[topic].splice(index, 1);
      }
    };
  },

  /**
   * Publish a message to a topic
   * @param {string} topic - The topic to publish to
   * @param {any} data - Data to pass to subscribers
   */
  publish(topic, data) {
    if (!this.subscribers[topic]) {
      return;
    }

    this.subscribers[topic].forEach(callback => {
      try {
        callback(topic, data);
      } catch (error) {
        console.error(`Error in subscriber for topic '${topic}':`, error);
      }
    });
  },

  /**
   * Clear all subscribers for a topic (or all topics if none specified)
   * @param {string} topic - Optional topic to clear
   */
  clear(topic) {
    if (topic) {
      this.subscribers[topic] = [];
    } else {
      this.subscribers = {};
    }
  },
};

export default messages;
