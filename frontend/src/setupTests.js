/**
 * Global test setup for Vitest
 * This file runs before each test file
 */
import '@testing-library/jest-dom'

// Mock window.matchMedia (used by Ant Design)
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => { },
        removeListener: () => { },
        addEventListener: () => { },
        removeEventListener: () => { },
        dispatchEvent: () => { }
    })
})

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', { value: localStorageMock })

// Mock URL.createObjectURL (used by export utilities)
URL.createObjectURL = vi.fn(() => 'blob:mock-url')
URL.revokeObjectURL = vi.fn()

// Mock i18next
vi.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key, fallback) => fallback || key,
        i18n: {
            language: 'en',
            changeLanguage: vi.fn()
        }
    }),
    Trans: ({ children }) => children,
    initReactI18next: {
        type: '3rdParty',
        init: () => { }
    }
}))

// Mock import.meta.env
vi.stubGlobal('import.meta', {
    env: {
        VITE_API_BASE_URL: 'http://localhost:8000',
        MODE: 'test'
    }
})
