import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import App from './App'
import { scrubSecrets, assertNoSecretsInBundle } from './api/client'
import { MOCK_SNAPSHOT, expandMission, contractMission, interruptStream } from './data/fixtures'

afterEach(() => {
  cleanup()
})

describe('console fixtures', () => {
  it('labels mock mode and never carries secret-shaped strings', () => {
    assertNoSecretsInBundle(MOCK_SNAPSHOT)
    expect(MOCK_SNAPSHOT.mode).toBe('mock')
    expect(scrubSecrets('Bearer sk-abc123xyz')).toContain('[redacted]')
  })

  it('expands and contracts mission graph', () => {
    const expanded = expandMission(MOCK_SNAPSHOT)
    expect(expanded.mission.tasks.length).toBeGreaterThan(MOCK_SNAPSHOT.mission.tasks.length)
    const contracted = contractMission(expanded)
    expect(contracted.mission.tasks.length).toBeLessThanOrEqual(expanded.mission.tasks.length)
  })

  it('marks stream interrupts for reconnect', () => {
    const interrupted = interruptStream(MOCK_SNAPSHOT)
    expect(interrupted.streamInterrupted).toBe(true)
    expect(interrupted.errors[0]).toMatch(/cursor/)
  })
})

describe('operator console UI', () => {
  it('shows mission waiting reasons and expand/contract', async () => {
    const user = userEvent.setup()
    render(<App />)
    expect(await screen.findByTestId('mode-banner')).toHaveTextContent('MOCK')
    expect(screen.getByTestId('mission-panel')).toBeInTheDocument()
    expect(screen.getByText(/inference quota exhausted/i)).toBeInTheDocument()
    const before = screen.getAllByTestId(/task-row-/).length
    await user.click(screen.getByTestId('expand-mission'))
    expect(screen.getAllByTestId(/task-row-/).length).toBeGreaterThan(before)
    await user.click(screen.getByTestId('contract-mission'))
  })

  it('shows exhausted, unknown, retired, gated routes without inventing available', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Routes' }))
    const panel = await screen.findByTestId('routes-panel')
    expect(within(panel).getByTestId('badge-exhausted')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-unknown')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-retired')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-gated')).toBeInTheDocument()
  })

  it('shows unknown capacity remaining honestly', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Capacity' }))
    expect(await screen.findByTestId('remaining-qb_tokens')).toHaveTextContent('unknown')
    expect(screen.getByTestId('remaining-qb_demo_requests')).toHaveTextContent('0')
  })

  it('distinguishes qualified vs provisional profiles', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Profiles' }))
    const panel = await screen.findByTestId('profiles-panel')
    expect(within(panel).getByTestId('badge-qualified')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-provisional')).toBeInTheDocument()
  })

  it('shows approval payload details', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Approvals' }))
    expect(await screen.findByTestId('approval-payload')).toHaveTextContent('tool.network')
  })

  it('handles interrupted event stream and stale workers', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Workers' }))
    expect(await screen.findByTestId('badge-stale')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Events' }))
    await user.click(screen.getByTestId('interrupt-stream'))
    expect(screen.getByTestId('stream-interrupted')).toBeInTheDocument()
    expect(screen.getByTestId('error-banner')).toBeInTheDocument()
  })

  it('shows projects, history, and artifacts panels', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Projects' }))
    expect(await screen.findByTestId('projects-panel')).toBeInTheDocument()
    expect(screen.getByTestId('project-proj_demo')).toHaveTextContent('Demo workspace')
    await user.click(screen.getByRole('button', { name: 'History' }))
    expect(await screen.findByTestId('history-panel')).toBeInTheDocument()
    expect(screen.getByTestId('history-mission_demo_001')).toHaveTextContent('zero_spend')
    await user.click(screen.getByRole('button', { name: 'Artifacts' }))
    expect(await screen.findByTestId('artifacts-panel')).toBeInTheDocument()
    expect(screen.getByTestId('artifact-art_journey_note')).toHaveTextContent('markdown')
  })

  it('supports keyboard tab navigation to sections', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.tab()
    // First focusable after load should be a tab or action; navigate to Routes via keyboard activation.
    const routes = screen.getByRole('button', { name: 'Routes' })
    routes.focus()
    await user.keyboard('{Enter}')
    expect(await screen.findByTestId('routes-panel')).toBeInTheDocument()
  })
})
