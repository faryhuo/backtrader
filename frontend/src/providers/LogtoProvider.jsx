import { LogtoProvider as LogtoReactProvider } from '@logto/react';
import PropTypes from 'prop-types';
import { useLogtoConfig } from '../contexts/LogtoConfigContext';

/**
 * Logto Authentication Provider
 *
 * Wraps the application with Logto authentication configuration.
 * Handles OAuth 2.0 authentication flow and token management.
 * Fetches configuration from backend API with fallback to environment variables.
 */
export function LogtoProvider({ children }) {
  const { config, loading, error } = useLogtoConfig();

  // Show loading state while fetching config
  if (loading) {
    return <div>Loading authentication configuration...</div>;
  }

  // If config failed to load and no fallback is available
  if (error && (!config || !config.endpoint || !config.appId)) {
    console.error(
      'Logto configuration missing. Please configure Logto settings or set environment variables.'
    );
    // Return children without Logto provider if login is disabled
    if (!config || !config.enableLogin) {
      return <>{children}</>;
    }
    return <div>Error loading authentication configuration</div>;
  }

  // This is separate from VITE_API_BASE_URL which is the HTTP API endpoint
  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api';

  // Prepare Logto configuration
  const logtoConfig = {
    endpoint: config.endpoint,
    appId: config.appId,
    resources: [apiBase],
  };

  // Validate configuration
  if (!logtoConfig.endpoint || !logtoConfig.appId) {
    console.error(
      'Logto configuration missing. Please set endpoint and appId in settings or .env file'
    );
  }

  return (
    <LogtoReactProvider config={logtoConfig}>
      {children}
    </LogtoReactProvider>
  );
}

LogtoProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
