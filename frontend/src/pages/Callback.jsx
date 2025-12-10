import { useEffect } from 'react';
import { useHandleSignInCallback } from '@logto/react';
import { useNavigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import './Callback.css';

/**
 * Authentication Callback Handler
 *
 * This page handles the redirect from Logto after successful authentication.
 * Processes the OAuth callback and redirects to the main application.
 */
export function Callback() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { isLoading, error } = useHandleSignInCallback(() => {
    // Redirect to main app after successful sign-in
    navigate('/', { replace: true });
  });

  // Handle errors
  useEffect(() => {
    if (error) {
      console.error('Sign-in callback error:', error);
      // Redirect to home page on error
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 3000);
    }
  }, [error, navigate]);

  return (
    <div className="callback-page">
      <Spin size="large" tip={t('auth.signingIn', 'Signing in...')} />
      {error && (
        <div className="callback-error">
          <p>{t('auth.signInError', 'Authentication failed. Redirecting...')}</p>
        </div>
      )}
    </div>
  );
}
