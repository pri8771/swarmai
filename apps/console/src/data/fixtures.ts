/** Deterministic fixture snapshot — clearly mock, never live spend. */

import type { ConsoleSnapshot } from '../api/types'

export const MOCK_SNAPSHOT: ConsoleSnapshot = {
  mode: 'mock',
  mockVsLive: 'console_fixtures_only_not_live_providers',
  hostnamePublic: 'swarm.splitsignal.ai',
  serverReady: null,
  mission: {
    missionId: 'mission_demo_001',
    revision: 3,
    status: 'running',
    objective: 'Investigate failing parser and produce a verified patch',
    planningRoles: ['planner-a', 'planner-b', 'verifier'],
    logicalAgents: 5,
    busyWorkers: 2,
    inFlightInference: 1,
    tasks: [
      {
        id: 'task_child_a',
        objective: 'Extract failing cases',
        status: 'running',
        roleHint: 'extractor',
      },
      {
        id: 'task_child_b',
        objective: 'Classify failure modes',
        status: 'waiting',
        roleHint: 'classifier',
        waitingReason: 'inference quota exhausted on shared bucket qb_demo_requests',
        unblockEvent: 'quota.reset or alternate route admission',
      },
      {
        id: 'task_child_c',
        objective: 'Draft patch',
        status: 'blocked',
        roleHint: 'coder',
        waitingReason: 'depends on task_child_a acceptance',
        unblockEvent: 'finding.accepted for task_child_a',
      },
    ],
  },
  routes: [
    {
      routeId: 'rt_fake_alpha',
      provider: 'fake',
      modelId: 'fake-alpha-v1',
      availability: 'available',
      status: 'mock_enabled',
      capabilityClaims: ['chat', 'tools'],
    },
    {
      routeId: 'rt_fake_beta',
      provider: 'fake',
      modelId: 'fake-beta-v1',
      availability: 'exhausted',
      status: 'quota_exhausted',
      capabilityClaims: ['chat', 'tools'],
    },
    {
      routeId: 'rt_fake_unknown',
      provider: 'fake',
      modelId: 'fake-unknown-v0',
      availability: 'unknown',
      status: 'cataloged',
      capabilityClaims: [],
    },
    {
      routeId: 'retired_github_models',
      provider: 'github_models',
      modelId: null,
      availability: 'retired',
      status: 'retired',
      capabilityClaims: [],
    },
    {
      routeId: 'rt_gated_canary',
      provider: 'openrouter',
      modelId: 'gated-canary',
      availability: 'gated',
      status: 'policy_gated',
      capabilityClaims: ['chat'],
    },
  ],
  capacity: [
    {
      bucketId: 'qb_demo_requests',
      dimension: 'requests',
      remaining: 0,
      limit: 100,
      note: 'shared upstream exhausted',
    },
    {
      bucketId: 'qb_tokens',
      dimension: 'total_tokens',
      remaining: null,
      limit: null,
      note: 'remaining unknown — do not invent headroom',
    },
  ],
  capacityUnknown: true,
  workers: [
    {
      workerId: 'wk_local_1',
      status: 'online',
      generation: 2,
      capacity: 2,
      privacy: ['local'],
      claimed: 'task_child_a',
      revoked: false,
    },
    {
      workerId: 'wk_stale_2',
      status: 'online',
      generation: 1,
      capacity: 1,
      privacy: ['local'],
      claimed: null,
      revoked: false,
      stale: true,
    },
  ],
  profiles: [
    {
      key: 'fake-alpha|extraction|small',
      taskFamily: 'extraction',
      sizeBand: 'small',
      state: 'qualified',
      wilsonLower: 0.91,
      distinctCases: 42,
    },
    {
      key: 'fake-beta|classification|medium',
      taskFamily: 'classification',
      sizeBand: 'medium',
      state: 'provisional',
      wilsonLower: 0.72,
      distinctCases: 4,
    },
  ],
  approvals: [
    {
      id: 'apr_demo_1',
      operation: 'tool.network',
      destination: 'https://example.invalid/hooks',
      payloadHash: 'abc123deadbeef',
      payloadPreview: { project_id: 'proj_demo', op: 'tool.network', url: 'https://example.invalid/hooks' },
      expiresAt: '2099-01-01T00:00:00Z',
      revokedAt: null,
    },
  ],
  projects: [
    {
      projectId: 'proj_demo',
      name: 'Demo workspace',
      repoPath: '/Users/pchordia/Downloads/swarm-ai',
      allowPaid: false,
      allowedTools: ['repo.read', 'tests.run', 'calc'],
      updatedAt: '2026-09-20T12:00:00Z',
    },
  ],
  history: [
    {
      missionId: 'mission_demo_001',
      projectId: 'proj_demo',
      goal: 'Investigate failing parser and produce a verified patch',
      status: 'completed',
      costUsd: 0,
      artifactCount: 2,
      tags: ['completed', 'zero_spend'],
      updatedAt: '2026-09-20T12:30:00Z',
    },
  ],
  artifacts: [
    {
      artifactId: 'art_journey_note',
      kind: 'markdown',
      uri: 'var/artifacts/mission_demo_001/journey_note.md',
      summary: 'V0.8 journey artifact',
    },
    {
      artifactId: 'report:mission-report.json',
      kind: 'report',
      uri: 'var/reports/missions/mission_demo_001/mission-report.json',
      summary: 'Machine mission report',
    },
  ],
  events: [
    { id: 'ev_1', type: 'mission.created', summary: 'mission_demo_001 created' },
    { id: 'ev_2', type: 'graph.committed', summary: 'revision 3 committed' },
    { id: 'ev_3', type: 'inference.settled', summary: 'rt_fake_beta exhausted' },
  ],
  streamInterrupted: false,
  errors: [],
}

export function expandMission(snap: ConsoleSnapshot): ConsoleSnapshot {
  return {
    ...snap,
    mission: {
      ...snap.mission,
      revision: snap.mission.revision + 1,
      tasks: [
        ...snap.mission.tasks,
        {
          id: `task_spawn_${snap.mission.revision + 1}`,
          objective: 'Newly spawned verification subproblem',
          status: 'ready',
          roleHint: 'verifier',
        },
      ],
      logicalAgents: snap.mission.logicalAgents + 1,
    },
  }
}

export function contractMission(snap: ConsoleSnapshot): ConsoleSnapshot {
  const tasks = snap.mission.tasks.filter((t) => t.status !== 'ready')
  return {
    ...snap,
    mission: {
      ...snap.mission,
      revision: snap.mission.revision + 1,
      tasks: tasks.length ? tasks : snap.mission.tasks.slice(0, 1),
      logicalAgents: Math.max(1, snap.mission.logicalAgents - 1),
    },
  }
}

export function interruptStream(snap: ConsoleSnapshot): ConsoleSnapshot {
  return {
    ...snap,
    streamInterrupted: true,
    errors: [...snap.errors, 'event stream interrupted — reconnect with after=cursor'],
  }
}
