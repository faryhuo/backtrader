import { useLogto } from '@logto/react';
import { Navigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import './PrivateRoute.css';

/**
 * Protected Route Component
 *
 * Wraps routes that require authentication.
 * Redirects unauthenticated users to the login page.
 */
export function PrivateRoute({ children }) {
  const { isAuthenticated } = useLogto();
  // Redirect to login page if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Render protected content if authenticated
  return children;
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
};
