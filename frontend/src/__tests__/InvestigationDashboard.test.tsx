import '@testing-library/jest-dom'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { InvestigationDashboard } from '@/components/InvestigationDashboard'
import { api } from '@/services/api'

// Mock the API module
vi.mock('@/services/api', () => ({
  api: {
    createInvestigation: vi.fn(),
  },
}))

describe('InvestigationDashboard', () => {
  it('renders search form', () => {
    const mockOnCreated = vi.fn()
    render(<InvestigationDashboard onInvestigationCreated={mockOnCreated} />)

    expect(screen.getByPlaceholderText(/Alice Johnson/i)).toBeTruthy()
  })

  it('submits investigation on form submission', async () => {
    const mockOnCreated = vi.fn()
    
    vi.mocked(api.createInvestigation).mockResolvedValue({
      investigation_id: 'test-id',
      subject_name: 'Alice Johnson',
    } as any)

    render(<InvestigationDashboard onInvestigationCreated={mockOnCreated} />)

    const input = screen.getByPlaceholderText(/Alice Johnson/i)
    fireEvent.change(input, { target: { value: 'Alice Johnson' } })

    const button = screen.getByRole('button', { name: /Create Investigation/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(mockOnCreated).toHaveBeenCalledWith('test-id')
    })
  })
})
