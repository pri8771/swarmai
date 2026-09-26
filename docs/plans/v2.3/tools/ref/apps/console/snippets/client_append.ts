
function opsEventFromApi(raw: Record<string, unknown>): OpsEventRow {
  return {
    eventId: String(raw.event_id ?? ''),
    kind: String(raw.kind ?? ''),
    component: String(raw.component ?? ''),
    projectId: raw.project_id == null ? null : String(raw.project_id),
    traceId: raw.trace_id == null ? null : String(raw.trace_id),
    at: String(raw.at ?? ''),
  }
}

function queueFromApi(raw: Record<string, unknown>): SchedulerQueueRow {
  return {
    projectId: String(raw.project_id ?? ''),
    weight: Number(raw.weight ?? 0),
    credit: Number(raw.credit ?? 0),
    running: Number(raw.running ?? 0),
    maxConcurrency: Number(raw.max_concurrency ?? 0),
    paused: raw.paused === true,
  }
}

/** Ops tab data. Mock → MOCK_OPS; live → GET /v1/ops/events + /v1/scheduler/queues (never fixtures). */
export async function loadOps(opts: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}): Promise<OpsView> {
  if (opts.mode === 'mock') {
    const view = structuredClone(MOCK_OPS)
    assertNoSecretsInBundle(view)
    return view
  }
  const view: OpsView = { mode: 'live', events: [], queues: [], queuesAvailable: false, errors: [] }
  if (!opts.baseUrl) {
    view.errors.push('ops_requires_baseUrl')
    return view
  }
  const base = opts.baseUrl.replace(/\/$/, '')
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  try {
    const events = await fetchJson(`${base}/v1/ops/events`, headers)
    if (events.ok) {
      const rows = (events.body as { events?: Array<Record<string, unknown>> }).events ?? []
      view.events = rows.map(opsEventFromApi)
    } else {
      view.errors.push(`ops_events_http_${events.status}`)
    }
    const queues = await fetchJson(`${base}/v1/scheduler/queues`, headers)
    if (queues.ok) {
      const rows = (queues.body as { projects?: Array<Record<string, unknown>> }).projects ?? []
      view.queues = rows.map(queueFromApi)
      view.queuesAvailable = true
    } else if (queues.status !== 404) {
      view.errors.push(`scheduler_queues_http_${queues.status}`)
    }
  } catch (e: unknown) {
    view.errors.push(e instanceof Error ? e.message : 'ops_load_failed')
  }
  return view
}

/** Live: POST /v1/workers/{id}/drain | /revoke. A 404 means the server lacks the route. */
export async function workerControl(opts: {
  baseUrl: string
  token?: string
  workerId: string
  action: 'drain' | 'revoke'
  reason?: string
}): Promise<{ available: boolean; drainState: string | null }> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  try {
    const payload = await mutateJson(
      `${base}/v1/workers/${encodeURIComponent(opts.workerId)}/${opts.action}`,
      headers,
      'POST',
      { reason: opts.reason ?? `operator_${opts.action}` },
    )
    return { available: true, drainState: String(payload.drain_state ?? 'unknown') }
  } catch (e: unknown) {
    if (e instanceof Error && e.message === 'api_error_404') {
      return { available: false, drainState: null }
    }
    throw e
  }
}
