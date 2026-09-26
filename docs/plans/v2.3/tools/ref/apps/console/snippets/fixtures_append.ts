
/** Deterministic Ops tab fixture — mock mode only. */
export const MOCK_OPS: OpsView = {
  mode: 'mock',
  events: [
    {
      eventId: 'oev_mock_1',
      kind: 'scheduler.decision',
      component: 'scheduler',
      projectId: 'proj_demo',
      traceId: 'tr_mock_1',
      at: '2026-09-01T00:00:00+00:00',
    },
    {
      eventId: 'oev_mock_2',
      kind: 'attempt.started',
      component: 'controller',
      projectId: 'proj_demo',
      traceId: 'tr_mock_1',
      at: '2026-09-01T00:00:01+00:00',
    },
  ],
  queues: [
    {
      projectId: 'proj_demo',
      weight: 1,
      credit: 0.25,
      running: 1,
      maxConcurrency: 4,
      paused: false,
    },
  ],
  queuesAvailable: true,
  errors: [],
}
