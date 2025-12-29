import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { Navbar } from '../Navbar'

vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../../../contexts/LogtoConfigContext', () => ({
  useLogtoConfig: vi.fn(),
}))

import { useAuth } from '../../../hooks/useAuth'
import { useLogtoConfig } from '../../../contexts/LogtoConfigContext'

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useLogtoConfig.mockReturnValue({ config: null })
  })

  it('navigates to /strategy when login is disabled', async () => {
    useAuth.mockReturnValue({
      signIn: vi.fn(),
      loginEnabled: false,
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
        <LocationDisplay />
      </MemoryRouter>
    )

    fireEvent.click(screen.getAllByText('landing.nav.login')[0])

    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('/strategy')
    })
  })

  it('calls signIn with redirectUri when login is enabled', () => {
    const signIn = vi.fn()
    useAuth.mockReturnValue({
      signIn,
      loginEnabled: true,
    })
    useLogtoConfig.mockReturnValue({
      config: { redirectUri: 'http://localhost:5173/callback' },
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
        <LocationDisplay />
      </MemoryRouter>
    )

    fireEvent.click(screen.getAllByText('landing.nav.login')[0])

    expect(signIn).toHaveBeenCalledWith('http://localhost:5173/callback')
    expect(screen.getByTestId('location')).toHaveTextContent('/')
  })
})

