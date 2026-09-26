/** Deterministic fixture snapshot — clearly mock, never live spend. */

import type { ConsoleSnapshot, OpsView } from '../api/types'

export const MOCK_SNAPSHOT: ConsoleSnapshot = {
  mode: 'mock',
  mockVsLive: 'console_fixtures_only_not_live_providers',
  hostnamePublic: 'swarm.splitsignal.ai',
  serverReady: null,
  goals: [
    {
      id: 'goal_demo_001',
      projectId: 'proj_demo',
      desiredOutcome: 'Ship a verified parser fix without expanding spend',
      verificationCriteria: ['tests pass', 'independent review accepted'],
      kind: 'finite',
      scope: { repo: 'swarm-ai' },
      constraints: { allow_paid: false },
      resourceEnvelope: {
        max_wall_time_seconds: 3600,
        max_model_calls: 50,
        max_graph_nodes: 50,
        max_active_sessions: 4,
        tools: ['sandbox.fs'],
      },
      authorityEnvelope: {
        allowed_capabilities: ['code.read', 'code.write', 'tests.run'],
        tools: ['sandbox.fs'],
        intervention: 'operator_may_pause_redirect_resume',
      },
      owner: 'operator',
      permittedAgents: ['planner-a', 'extractor', 'coder', 'verifier'],
      strategy: 'Extract failing cases, classify, draft patch, verify',
      evidenceRefs: ['art_journey_note'],
      missionIds: ['mission_demo_001'],
      dependencies: [],
      missionOutcomes: [
        {
          at: '2026-09-20T12:20:00Z',
          mission_id: 'mission_demo_001',
          outcome: 'completed',
          actor: 'operator',
          notes: 'mission accepted — goal not yet achieved',
          evidence_refs: ['art_journey_note'],
        },
      ],
      openQuestions: ['Is the failure limited to nested objects?'],
      blockers: ['inference quota exhausted on shared bucket qb_demo_requests'],
      stopConditions: ['budget_exhausted', 'operator_cancel'],
      reviewCadence: 'on_mission_complete',
      expiresAt: null,
      status: 'active',
      progress: [
        {
          at: '2026-09-20T12:15:00Z',
          actor: 'pursuit',
          summary: 'act',
          metrics: { newly_met: ['tests pass'] },
        },
      ],
      decisionHistory: [
        {
          at: '2026-09-20T12:00:00Z',
          actor: 'operator',
          action: 'pause',
          from: 'active',
          to: 'paused',
          reason: 'interrupt:wait for quota',
        },
        {
          at: '2026-09-20T12:10:00Z',
          actor: 'operator',
          action: 'resume',
          from: 'paused',
          to: 'active',
          reason: 'resume:quota reset observed',
        },
      ],
      triggerReceipts: [],
      restartCount: 0,
      createdAt: '2026-09-20T11:00:00Z',
      updatedAt: '2026-09-20T12:20:00Z',
      pursuit: {
        goal_id: 'goal_demo_001',
        schedule: { wait_reason: null, backoff_seconds: 0 },
        history: [
          {
            cycle_id: 'cyc_demo_1',
            phase: 'update',
            decided_kind: 'act',
            notes: 'linked mission_demo_001',
            at: '2026-09-20T12:15:00Z',
          },
        ],
        commitments: [],
        adopted_lessons: [],
      },
    },
  ],
  selectedGoalId: 'goal_demo_001',
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
      activeLeases: ['lease_demo_1'],
      revoked: false,
    },
    {
      workerId: 'wk_stale_2',
      status: 'online',
      generation: 1,
      capacity: 1,
      privacy: ['local'],
      claimed: null,
      activeLeases: [],
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
