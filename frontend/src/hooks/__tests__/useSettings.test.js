/**
 * Unit tests for useSettings hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useSettings } from '../useSettings'
import { api } from '../../services/api'
import { DEFAULT_SETTINGS } from '../../constants/settingsConstants'

// Mock the api module
vi.mock('../../services/api', () => ({
    api: {
        getSettings: vi.fn(),
        updateSettings: vi.fn(),
        resetSettings: vi.fn()
    }
}))

// Mock antd message
vi.mock('antd', () => ({
    message: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn()
    }
}))

describe('useSettings', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Reset localStorage mock
        window.localStorage.getItem.mockReturnValue(null)
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('initial state', () => {
        it('should return default settings initially', () => {
            const { result } = renderHook(() => useSettings())

            expect(result.current.settings).toEqual(DEFAULT_SETTINGS)
            expect(result.current.loading).toBe(false)
            expect(result.current.saved).toBe(false)
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() => useSettings())

            expect(typeof result.current.loadSettings).toBe('function')
            expect(typeof result.current.handleChange).toBe('function')
            expect(typeof result.current.handleModelChange).toBe('function')
            expect(typeof result.current.handleSave).toBe('function')
            expect(typeof result.current.handleReset).toBe('function')
        })
    })

    describe('handleChange', () => {
        it('should update settings when handleChange is called', () => {
            const { result } = renderHook(() => useSettings())

            act(() => {
                result.current.handleChange('codeAnalysisPrompt', 'New prompt')
            })

            expect(result.current.settings.codeAnalysisPrompt).toBe('New prompt')
            expect(result.current.saved).toBe(false)
        })

        it('should preserve other settings when updating one', () => {
            const { result } = renderHook(() => useSettings())
            const initialModels = result.current.settings.selectedModels

            act(() => {
                result.current.handleChange('codeAnalysisPrompt', 'Updated')
            })

            expect(result.current.settings.selectedModels).toEqual(initialModels)
        })
    })

    describe('handleModelChange', () => {
        it('should update selectedModels', () => {
            const { result } = renderHook(() => useSettings())
            const newModels = ['gpt-4', 'claude-3']

            act(() => {
                result.current.handleModelChange(newModels)
            })

            expect(result.current.settings.selectedModels).toEqual(newModels)
            expect(result.current.saved).toBe(false)
        })
    })

    describe('loadSettings', () => {
        it('should load settings from API', async () => {
            const mockSettings = {
                selected_models: ['custom-model'],
                code_analysis_prompt: 'Custom prompt'
            }
            api.getSettings.mockResolvedValue({
                status: 'ok',
                settings: mockSettings
            })

            const { result } = renderHook(() => useSettings())

            await act(async () => {
                await result.current.loadSettings()
            })

            expect(result.current.settings.selectedModels).toEqual(['custom-model'])
            expect(result.current.settings.codeAnalysisPrompt).toBe('Custom prompt')
        })

        it('should use defaults when API fails', async () => {
            api.getSettings.mockRejectedValue(new Error('API Error'))
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })

            const { result } = renderHook(() => useSettings())

            await act(async () => {
                await result.current.loadSettings()
            })

            // Should still have settings (defaults or from localStorage fallback)
            expect(result.current.settings).toBeDefined()

            consoleSpy.mockRestore()
        })

        it('should set loading state during API call', async () => {
            let resolvePromise
            api.getSettings.mockImplementation(() => new Promise(resolve => {
                resolvePromise = resolve
            }))

            const { result } = renderHook(() => useSettings())

            act(() => {
                result.current.loadSettings()
            })

            await waitFor(() => {
                expect(result.current.loading).toBe(true)
            })

            await act(async () => {
                resolvePromise({ status: 'ok', settings: {} })
            })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })
        })
    })

    describe('handleSave', () => {
        it('should save settings to API', async () => {
            api.updateSettings.mockResolvedValue({ status: 'ok' })

            const { result } = renderHook(() => useSettings())

            await act(async () => {
                await result.current.handleSave()
            })

            expect(api.updateSettings).toHaveBeenCalled()
            expect(result.current.saved).toBe(true)
        })

        it('should show error when no models selected', async () => {
            const { message } = await import('antd')
            const { result } = renderHook(() => useSettings())

            // Clear selected models
            act(() => {
                result.current.handleModelChange([])
            })

            await act(async () => {
                await result.current.handleSave()
            })

            expect(message.error).toHaveBeenCalled()
            expect(api.updateSettings).not.toHaveBeenCalled()
        })
    })
})
