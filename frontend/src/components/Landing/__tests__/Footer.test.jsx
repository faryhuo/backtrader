import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Footer } from '../Footer'

vi.mock('../../../contexts/SiteConfigContext', () => ({
  useSiteConfig: vi.fn(),
}))

import { useSiteConfig } from '../../../contexts/SiteConfigContext'

describe('Footer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders fallback social links when config links are empty', () => {
    useSiteConfig.mockReturnValue({
      config: {
        site: { title: 'Backtrader Pro', description: '' },
        links: { docs: '', github: '', twitter: '', email: '' },
      },
      loading: false,
    })

    const { container } = render(<Footer />)

    expect(container.querySelector('a[href="https://github.com"]')).toBeInTheDocument()
    expect(container.querySelector('a[href="https://twitter.com"]')).toBeInTheDocument()
    expect(container.querySelector('a[href="mailto:contact@example.com"]')).toBeInTheDocument()
  })

  it('uses configured links when provided', () => {
    useSiteConfig.mockReturnValue({
      config: {
        site: { title: 'Acme Trading', description: '' },
        links: {
          docs: 'https://docs.example.com',
          github: 'https://github.com/acme',
          twitter: 'https://twitter.com/acme',
          email: 'support@example.com',
        },
      },
      loading: false,
    })

    const { container } = render(<Footer />)

    expect(container.querySelector('a[href="https://github.com/acme"]')).toBeInTheDocument()
    expect(container.querySelector('a[href="https://twitter.com/acme"]')).toBeInTheDocument()
    expect(container.querySelector('a[href="mailto:support@example.com"]')).toBeInTheDocument()

    expect(container.querySelector('a[href="https://github.com"]')).not.toBeInTheDocument()
    expect(container.querySelector('a[href="https://twitter.com"]')).not.toBeInTheDocument()
    expect(container.querySelector('a[href="mailto:contact@example.com"]')).not.toBeInTheDocument()

    const docsLink = screen.getByText('landing.footer.resources.docs').closest('a')
    expect(docsLink).toHaveAttribute('href', 'https://docs.example.com')
  })
})

