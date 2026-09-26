
export interface OpsEventRow {
  eventId: string
  kind: string
  component: string
  projectId: string | null
  traceId: string | null
  at: string
}

export interface SchedulerQueueRow {
  projectId: string
  weight: number
  credit: number
  running: number
  maxConcurrency: number
  paused: boolean
}

export interface OpsView {
  mode: 'mock' | 'live'
  events: OpsEventRow[]
  queues: SchedulerQueueRow[]
  /** False when the server has no /v1/scheduler/queues (404) — shown honestly, never faked. */
  queuesAvailable: boolean
  errors: string[]
}
