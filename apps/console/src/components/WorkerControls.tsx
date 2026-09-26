import { useState } from 'react'
import { workerControl } from '../api/client'
import type { WorkerRow } from '../api/types'

export function WorkerControls({
  workers,
  mode,
  baseUrl,
  token,
}: {
  workers: WorkerRow[]
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}) {
  const [busy, setBusy] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)
  const disabled = !!busy || mode !== 'live' || !baseUrl

  const run = (workerId: string, action: 'drain' | 'revoke') => {
    if (!baseUrl) return
    setBusy(`${action}:${workerId}`)
    setNote(null)
    void workerControl({ baseUrl, token, workerId, action, reason: `console_operator_${action}` })
      .then((res) => {
        setNote(
          res.available
            ? `${workerId} → ${res.drainState}`
            : `${action === 'drain' ? 'Drain' : 'Revoke'} not available on this server`,
        )
      })
      .catch((e: unknown) => setNote(e instanceof Error ? e.message : `${action}_failed`))
      .finally(() => setBusy(null))
  }

  return (
    <div data-testid="worker-controls">
      <h3>Worker drain / revoke</h3>
      {mode !== 'live' ? (
        <p className="muted" data-testid="worker-controls-mock">
          Fixture mode: controls disabled. Live controls call the authenticated API.
        </p>
      ) : null}
      {note ? <p data-testid="worker-controls-note">{note}</p> : null}
      <table className="grid">
        <thead>
          <tr>
            <th>Worker</th>
            <th>Status</th>
            <th>Control</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((w) => (
            <tr key={w.workerId} data-testid={`ops-worker-${w.workerId}`}>
              <td>
                <code>{w.workerId}</code>
              </td>
              <td>{w.revoked ? 'revoked' : w.status}</td>
              <td>
                <button
                  type="button"
                  data-testid={`drain-${w.workerId}`}
                  disabled={disabled || w.revoked}
                  onClick={() => run(w.workerId, 'drain')}
                >
                  Drain
                </button>{' '}
                <button
                  type="button"
                  data-testid={`revoke-${w.workerId}`}
                  disabled={disabled || w.revoked}
                  onClick={() => run(w.workerId, 'revoke')}
                >
                  Revoke
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {workers.length === 0 ? <p data-testid="ops-no-workers">No workers enrolled.</p> : null}
    </div>
  )
}
