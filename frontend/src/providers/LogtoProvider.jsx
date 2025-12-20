import { LogtoProvider as LogtoReactProvider } from '@logto/react';
import PropTypes from 'prop-types';

/**
 * Logto Authentication Provider
 *
 * Wraps the application with Logto authentication configuration.
 * Handles OAuth 2.0 authentication flow and token management.
 */
export function LogtoProvider({ children }) {
  const config = {
    endpoint: import.meta.env.VITE_LOGTO_ENDPOINT,
    appId: import.meta.env.VITE_LOGTO_APP_ID,
    // This is separate from VITE_API_BASE_URL which is the HTTP API endpoint
    resources: [import.meta.env.VITE_API_BASE_URL],
  };

  // Validate configuration
  if (!config.endpoint || !config.appId) {
    console.error(
      'Logto configuration missing. Please set VITE_LOGTO_ENDPOINT and VITE_LOGTO_APP_ID in .env file'
    );
  }

  return (
    <LogtoReactProvider config={config}>
      {children}
    </LogtoReactProvider>
  );
}

LogtoProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
