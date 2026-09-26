import { useEffect, useState } from 'react'
import { loadOps } from '../api/client'
import type { OpsView, WorkerRow } from '../api/types'
import { Panel } from './Panel'
import { WorkerControls } from './WorkerControls'

export function OpsPanel({
  mode,
  baseUrl,
  token,
  workers,
}: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
  workers: WorkerRow[]
}) {
  const [view, setView] = useState<OpsView | null>(null)

  useEffect(() => {
    let cancelled = false
    void loadOps({ mode, baseUrl, token }).then((v) => {
      if (!cancelled) setView(v)
    })
    return () => {
      cancelled = true
    }
  }, [mode, baseUrl, token])

  return (
    <Panel
      title="Operations"
      subtitle="Read-only scheduler and ops events; mutations only via the authenticated API"
      testId="ops-panel"
    >
      {view === null ? <p data-testid="ops-loading">Loading ops…</p> : null}
      {view && view.errors.length > 0 ? (
        <div className="banner-error" role="alert" data-testid="ops-errors">
          {view.errors.map((e) => (
            <p key={e}>{e}</p>
          ))}
        </div>
      ) : null}
      {view ? (
        <>
          <h3>Scheduler queues</h3>
          {view.queuesAvailable ? (
            <table className="grid" data-testid="ops-queues">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Weight</th>
                  <th>Credit</th>
                  <th>Running / max</th>
                  <th>Paused</th>
                </tr>
              </thead>
              <tbody>
                {view.queues.map((q) => (
                  <tr key={q.projectId} data-testid={`ops-queue-${q.projectId}`}>
                    <td>
                      <code>{q.projectId}</code>
                    </td>
                    <td>{q.weight}</td>
                    <td>{q.credit.toFixed(3)}</td>
                    <td>
                      {q.running} / {q.maxConcurrency}
                    </td>
                    <td>{q.paused ? 'yes' : 'no'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="muted" data-testid="ops-queues-unavailable">
              Scheduler queues not available on this server.
            </p>
          )}
          <h3>Ops events</h3>
          <table className="grid" data-testid="ops-events">
            <thead>
              <tr>
                <th>At</th>
                <th>Kind</th>
                <th>Component</th>
                <th>Project</th>
                <th>Trace</th>
              </tr>
            </thead>
            <tbody>
              {view.events.map((e) => (
                <tr key={e.eventId} data-testid={`ops-event-${e.eventId}`}>
                  <td>{e.at}</td>
                  <td>
                    <code>{e.kind}</code>
                  </td>
                  <td>{e.component}</td>
                  <td>{e.projectId ?? '—'}</td>
                  <td>{e.traceId ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {view.events.length === 0 ? <p data-testid="ops-no-events">No ops events.</p> : null}
        </>
      ) : null}
      <WorkerControls workers={workers} mode={mode} baseUrl={baseUrl} token={token} />
    </Panel>
  )
}
