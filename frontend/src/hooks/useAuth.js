import { useLogto } from '@logto/react';
import { useLogtoConfig } from '../contexts/LogtoConfigContext';

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
  const { config, loading } = useLogtoConfig();

  // Show loading state while config is being fetched
  if (loading) {
    return {
      ...ANONYMOUS_AUTH,
      isLoading: true,
    };
  }

  // Return early when login is disabled - LogtoProvider is not present
  const loginEnabled = config?.enableLogin ?? false;
  if (!loginEnabled) {
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
