import { Navigate, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import { Spin } from 'antd';
import { useAuth } from '../../hooks/useAuth';
import './PrivateRoute.css';

/**
 * Protected Route Component
 *
 * Wraps routes that require authentication.
 * Redirects unauthenticated users to the login page.
 */
export function PrivateRoute({ children }) {
  const location = useLocation();
  const { isAuthenticated, loginEnabled, isLoading } = useAuth();

  // Authentication disabled - allow direct access.
  if (!loginEnabled) {
    return children;
  }

  if (isLoading) {
    return <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}><Spin size="large" /></div>;
  }

  // Redirect to login page if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Render protected content if authenticated
  return children;
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
};
