import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

export function useAuthContext() {
    const context = useContext(AuthContext)
    if (context === null) {
        throw new Error('useAuthContext must be used within AuthContext provider')
    }
    return context
}
