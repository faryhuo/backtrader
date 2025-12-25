/**
 * Unit tests for SettingsContext
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { SettingsProvider, useSettingsContext } from '../SettingsContext'

// Mock the api module
vi.mock('../../services/api', () => ({
    api: {
        getSettings: vi.fn()
    }
}))

// Import after mocking
import { api } from '../../services/api'
import { DEFAULT_SETTINGS } from '../../constants/settingsConstants'

describe('SettingsContext', () => {
    const mockApiSettings = {
        status: 'ok',
        settings: {
            selected_models: ['gpt-4o'],
            code_analysis_prompt: 'Custom analysis prompt',
            code_rewrite_prompt: 'Custom rewrite prompt',
            full_strategy_analysis_prompt: 'Custom strategy prompt'
        }
    }

    const wrapper = ({ children }) => (
        <SettingsProvider>{children}</SettingsProvider>
    )

    beforeEach(() => {
        vi.clearAllMocks()
        localStorage.clear()
    })

    afterEach(() => {
        vi.restoreAllMocks()
        localStorage.clear()
    })

    describe('initial state and loading', () => {
        it('should load settings from API successfully', async () => {
            api.getSettings.mockResolvedValue(mockApiSettings)

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            expect(result.current.loading).toBe(true)

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings).toEqual({
                selectedModels: ['gpt-4o'],
                codeAnalysisPrompt: 'Custom analysis prompt',
                codeRewritePrompt: 'Custom rewrite prompt',
                fullStrategyAnalysisPrompt: 'Custom strategy prompt'
            })
            expect(api.getSettings).toHaveBeenCalledTimes(1)
        })

        it('should sync API settings to localStorage', async () => {
            api.getSettings.mockResolvedValue(mockApiSettings)

            renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                const stored = localStorage.getItem('userSettings')
                expect(stored).toBeTruthy()
            })

            const storedSettings = JSON.parse(localStorage.getItem('userSettings'))
            expect(storedSettings).toEqual({
                selectedModels: ['gpt-4o'],
                codeAnalysisPrompt: 'Custom analysis prompt',
                codeRewritePrompt: 'Custom rewrite prompt',
                fullStrategyAnalysisPrompt: 'Custom strategy prompt'
            })
        })

        it('should fallback to localStorage when API fails', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            const localStorageSettings = {
                selectedModels: ['gpt-4o-mini'],
                codeAnalysisPrompt: 'Local prompt'
            }

            localStorage.setItem('userSettings', JSON.stringify(localStorageSettings))
            api.getSettings.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings).toMatchObject(localStorageSettings)

            consoleError.mockRestore()
        })

        it('should use defaults when API fails and localStorage is empty', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })
            api.getSettings.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings).toEqual(DEFAULT_SETTINGS)

            consoleError.mockRestore()
        })

        it('should handle API response with missing status', async () => {
            api.getSettings.mockResolvedValue({ status: 'error' })

            localStorage.setItem('userSettings', JSON.stringify({
                selectedModels: ['cached-model']
            }))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings.selectedModels).toContain('cached-model')
        })
    })

    describe('settings migration', () => {
        it('should migrate old aiModel to selectedModels array', async () => {
            api.getSettings.mockRejectedValue(new Error('No API'))

            const oldSettings = {
                aiModel: 'gpt-4',
                codeAnalysisPrompt: 'Old prompt'
            }

            localStorage.setItem('userSettings', JSON.stringify(oldSettings))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings.selectedModels).toEqual(['gpt-4'])
            expect(result.current.settings.aiModel).toBeUndefined()
            expect(result.current.settings.codeAnalysisPrompt).toBe('Old prompt')
        })

        it('should not migrate if selectedModels already exists', async () => {
            api.getSettings.mockRejectedValue(new Error('No API'))

            const newSettings = {
                selectedModels: ['gpt-4o'],
                aiModel: 'old-model', // Should be ignored
                codeAnalysisPrompt: 'Prompt'
            }

            localStorage.setItem('userSettings', JSON.stringify(newSettings))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings.selectedModels).toEqual(['gpt-4o'])
        })
    })

    describe('getAvailableModels', () => {
        it('should return configured models', async () => {
            api.getSettings.mockResolvedValue(mockApiSettings)

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            const models = result.current.getAvailableModels()
            expect(models).toEqual(['gpt-4o'])
        })

        it('should return default models when selectedModels is empty', async () => {
            api.getSettings.mockResolvedValue({
                status: 'ok',
                settings: {
                    selected_models: [],
                    code_analysis_prompt: 'Prompt'
                }
            })

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            const models = result.current.getAvailableModels()
            expect(models).toEqual(DEFAULT_SETTINGS.selectedModels)
        })

        it('should return default models when selectedModels is null', async () => {
            api.getSettings.mockResolvedValue({
                status: 'ok',
                settings: {
                    selected_models: null
                }
            })

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            const models = result.current.getAvailableModels()
            expect(models).toEqual(DEFAULT_SETTINGS.selectedModels)
        })
    })

    describe('refreshSettings', () => {
        it('should reload settings from API', async () => {
            api.getSettings
                .mockResolvedValueOnce(mockApiSettings)
                .mockResolvedValueOnce({
                    status: 'ok',
                    settings: {
                        selected_models: ['claude-3-5-sonnet-20241022'],
                        code_analysis_prompt: 'Updated prompt'
                    }
                })

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings.selectedModels).toEqual(['gpt-4o'])

            act(() => {
                result.current.refreshSettings()
            })

            expect(result.current.loading).toBe(true)

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.settings.selectedModels).toEqual(['claude-3-5-sonnet-20241022'])
            expect(result.current.settings.codeAnalysisPrompt).toBe('Updated prompt')
            expect(api.getSettings).toHaveBeenCalledTimes(2)
        })

        it('should update loading state during refresh', async () => {
            api.getSettings.mockResolvedValue(mockApiSettings)

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            act(() => {
                result.current.refreshSettings()
            })

            expect(result.current.loading).toBe(true)

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })
        })
    })

    describe('localStorage error handling', () => {
        it('should handle localStorage read errors gracefully', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            // Mock localStorage.getItem to throw
            const originalGetItem = localStorage.getItem
            localStorage.getItem = vi.fn().mockImplementation(() => {
                throw new Error('LocalStorage error')
            })

            api.getSettings.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            // Should fall back to defaults
            expect(result.current.settings).toEqual(DEFAULT_SETTINGS)

            localStorage.getItem = originalGetItem
            consoleError.mockRestore()
        })

        it('should handle corrupted localStorage data', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            localStorage.setItem('userSettings', 'invalid-json{{{')
            api.getSettings.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() => useSettingsContext(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            // Should fall back to defaults
            expect(result.current.settings).toEqual(DEFAULT_SETTINGS)

            consoleError.mockRestore()
        })
    })

    describe('useSettingsContext outside provider', () => {
        it('should return defaults when used outside provider', () => {
            const { result } = renderHook(() => useSettingsContext())

            expect(result.current.settings).toEqual(DEFAULT_SETTINGS)
            expect(result.current.loading).toBe(false)
            expect(typeof result.current.getAvailableModels).toBe('function')
            expect(typeof result.current.refreshSettings).toBe('function')
        })

        it('should return default models from getAvailableModels', () => {
            const { result } = renderHook(() => useSettingsContext())

            const models = result.current.getAvailableModels()
            expect(models).toEqual(DEFAULT_SETTINGS.selectedModels)
        })

        it('should not throw when calling refreshSettings outside provider', () => {
            const { result } = renderHook(() => useSettingsContext())

            expect(() => {
                result.current.refreshSettings()
            }).not.toThrow()
        })
    })
})
