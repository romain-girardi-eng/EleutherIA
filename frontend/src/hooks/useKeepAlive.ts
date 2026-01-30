import { useEffect } from 'react';

/**
 * Keep-Alive Hook
 *
 * Maintains backend connection health by periodically pinging the health endpoint,
 * but ONLY when the user is actively using the application.
 *
 * Ethical design:
 * - Only pings when user has been active in the last 5 minutes
 * - Stops pinging when user is idle or closes tab
 * - Uses HEAD request to minimize bandwidth
 * - Silently fails if backend is unreachable
 */
export const useKeepAlive = () => {
  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    let lastActivity = Date.now();

    // Track user activity
    const updateActivity = () => {
      lastActivity = Date.now();
    };

    // Listen to various user interactions
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach(event => {
      window.addEventListener(event, updateActivity, { passive: true });
    });

    // Keep-alive ping function
    const pingBackend = async () => {
      const inactiveDuration = Date.now() - lastActivity;
      const fiveMinutes = 5 * 60 * 1000;

      // Only ping if user was active in the last 5 minutes
      if (inactiveDuration < fiveMinutes) {
        try {
          // Use GET request - backend health endpoint doesn't support HEAD
          await fetch(`${apiUrl}/api/health`, {
            method: 'GET',
          });
          console.debug('✅ Keep-alive ping sent');
        } catch (_error) {
          // Silently fail - don't disrupt user experience
          console.debug('⚠️ Keep-alive ping failed (expected if offline)');
        }
      } else {
        console.debug('⏸️ User inactive, skipping keep-alive ping');
      }
    };

    // Start pinging every 10 minutes
    const keepAliveInterval = window.setInterval(pingBackend, 10 * 60 * 1000);

    // Also ping immediately if user becomes active after being idle
    let wasInactive = false;
    const checkInactivity = () => {
      const inactiveDuration = Date.now() - lastActivity;
      const tenMinutes = 10 * 60 * 1000;

      if (inactiveDuration > tenMinutes && !wasInactive) {
        wasInactive = true;
      } else if (inactiveDuration < 1000 && wasInactive) {
        // User just became active again
        wasInactive = false;
        pingBackend(); // Immediate ping to wake backend
        console.debug('🔄 User active after idle period, waking backend');
      }
    };

    const inactivityChecker = window.setInterval(checkInactivity, 30 * 1000); // Check every 30s

    // Cleanup
    return () => {
      clearInterval(keepAliveInterval);
      clearInterval(inactivityChecker);
      events.forEach(event => {
        window.removeEventListener(event, updateActivity);
      });
    };
  }, []);
};
