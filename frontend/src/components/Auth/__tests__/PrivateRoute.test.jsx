import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { PrivateRoute } from '../PrivateRoute'

vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '../../../hooks/useAuth'

function renderPrivateRoute() {
  render(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route
          path="/protected"
          element={
            <PrivateRoute>
              <div>Protected Content</div>
            </PrivateRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  )
}

describe('PrivateRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children when login is disabled', () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      loginEnabled: false,
    })

    renderPrivateRoute()

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })

  it('redirects to /login when not authenticated', () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      loginEnabled: true,
    })

    renderPrivateRoute()

    expect(screen.getByText('Login Page')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      loginEnabled: true,
    })

    renderPrivateRoute()

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })
})

