import { useLogto } from '@logto/react';
import { LOGIN_ENABLED } from '../config/auth';

const ANONYMOUS_AUTH = {
  loginEnabled: false,
  isAuthenticated: true,
  isLoading: false,
  error: null,
  signIn: () => {},
  signOut: () => {},
  getAccessToken: async () => null,
  getIdTokenClaims: async () => ({}),
};

/**
 * Unified auth hook that supports both protected and anonymous modes.
 * When login is disabled, returns no-op auth handlers while reporting authenticated.
 */
export function useAuth() {
  if (!LOGIN_ENABLED) {
    return ANONYMOUS_AUTH;
  }

  const logto = useLogto();
  return {
    ...logto,
    loginEnabled: true,
  };
}
