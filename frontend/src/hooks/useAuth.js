import { useLogto } from '@logto/react';
import { LOGIN_ENABLED } from '../config/auth';

const ANONYMOUS_AUTH = {
  loginEnabled: false,
  isAuthenticated: true,
  isLoading: false,
  error: null,
  signIn: () => { },
  signOut: () => { },
  getAccessToken: async () => null,
  getIdTokenClaims: async () => ({}),
};

/**
 * Unified auth hook that supports both protected and anonymous modes.
 * When login is disabled, returns no-op auth handlers while reporting authenticated.
 * 
 * Note: We must return early before calling useLogto() when login is disabled,
 * because the LogtoProvider is not present in the component tree in that case.
 */
export function useAuth() {
  // Return early when login is disabled - LogtoProvider is not present
  if (!LOGIN_ENABLED) {
    return ANONYMOUS_AUTH;
  }

  // Only call useLogto when we know LogtoProvider exists in the tree
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const logto = useLogto();

  return {
    ...logto,
    loginEnabled: true,
  };
}
