import { useAuthContext } from '../contexts/AuthContext'

export function useAuth() {
    return useAuthContext()
}
