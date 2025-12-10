import { Navigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useAuth } from '../../hooks/useAuth';
import './PrivateRoute.css';

/**
 * Protected Route Component
 *
 * Wraps routes that require authentication.
 * Redirects unauthenticated users to the login page.
 */
export function PrivateRoute({ children }) {
  const { isAuthenticated, loginEnabled } = useAuth();

  // Authentication disabled - allow direct access.
  if (!loginEnabled) {
    return children;
  }

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
