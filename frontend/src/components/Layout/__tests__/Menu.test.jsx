import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Menu from '../Menu'

describe('Menu', () => {
  it('treats /strategy as active on root route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Menu collapsed={false} setCollapsed={vi.fn()} />
      </MemoryRouter>
    )

    const runStrategyLink = screen.getByTitle('nav.run_strategy')
    expect(runStrategyLink).toHaveClass('active')
  })

  it('marks current route link as active', () => {
    render(
      <MemoryRouter initialEntries={['/history']}>
        <Menu collapsed={false} setCollapsed={vi.fn()} />
      </MemoryRouter>
    )

    expect(screen.getByTitle('nav.history')).toHaveClass('active')
    expect(screen.getByTitle('nav.run_strategy')).not.toHaveClass('active')
  })

  it('hides group headers and text when collapsed', () => {
    render(
      <MemoryRouter initialEntries={['/strategy']}>
        <Menu collapsed={true} setCollapsed={vi.fn()} />
      </MemoryRouter>
    )

    expect(screen.queryByText('nav.group_strategy')).not.toBeInTheDocument()
    expect(screen.queryByText('nav.run_strategy')).not.toBeInTheDocument()
  })

  it('calls setCollapsed with toggled value', () => {
    const setCollapsed = vi.fn()

    render(
      <MemoryRouter initialEntries={['/strategy']}>
        <Menu collapsed={false} setCollapsed={setCollapsed} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByTitle('common.collapse_sidebar'))
    expect(setCollapsed).toHaveBeenCalledWith(true)
  })
})

