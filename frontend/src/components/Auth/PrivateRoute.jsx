import { useLogto } from '@logto/react';
import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import PropTypes from 'prop-types';
import './PrivateRoute.css';

/**
 * Protected Route Component
 *
 * Wraps routes that require authentication.
 * Redirects unauthenticated users to the home page.
 * Shows loading spinner while checking authentication status.
 */
export function PrivateRoute({ children }) {
  const { isAuthenticated, isLoading } = useLogto();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="private-route-loading">
        <Spin size="large" tip="Loading..." />
      </div>
    );
  }

  // Redirect to home page if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Render protected content if authenticated
  return children;
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
};
