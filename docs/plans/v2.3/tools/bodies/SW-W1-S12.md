**Goal.** Implement V20-E09 console parity for V2.3 operations.
- Add a read-only **Ops** tab showing the scheduler queues and ops events.
- Add worker **drain / revoke** controls that call the authenticated API, which is the action boundary.

The server endpoints come from SW-W3-S1: `GET /v1/scheduler/queues`, and `POST /v1/workers/{id}/drain` and `/revoke`. They may not exist yet, so the UI must handle a **404 honestly**: show "not available", and never fake data. Live mode never falls back to fixtures; mock mode (`?mode=mock`) uses `MOCK_OPS`.

**API shapes this UI expects.** SW-W3-S1 implements exactly these:
- `GET /v1/ops/events` → `{"events": [{"event_id","kind","component","project_id","trace_id","at",...}]}`. This already exists.
- `GET /v1/scheduler/queues` → `{"projects": [{"project_id","weight","credit","running","max_concurrency","paused"}]}`.
- `POST /v1/workers/{worker_id}/drain` and `/revoke`, body `{"reason": str}` → `{"worker_id","drain_state"}`.

The code below was run against `dev @ 8e1c0fde`: `npm run lint` shows 0 errors and only the 2 existing warnings, `npm run test` gives 26 passed (5 new), and `npm run build` succeeds. Work inside `apps/console`. **No Python changes.**

### Step 1 — `apps/console/src/api/types.ts` (append at the very end of the file, exactly)
```ts
{{FILE:apps/console/snippets/types_append.ts}}
```

### Step 2 — `apps/console/src/api/client.ts`
(a) Replace the import block at the top of the file. Find exactly:
```ts
  MissionTask,
  PursuitStatus,
} from './types'
import { MOCK_SNAPSHOT } from '../data/fixtures'
```
and replace it with:
```ts
  MissionTask,
  OpsEventRow,
  OpsView,
  PursuitStatus,
  SchedulerQueueRow,
} from './types'
import { MOCK_OPS, MOCK_SNAPSHOT } from '../data/fixtures'
```
(b) Append the following at the very end of the file, exactly. It reuses the existing private helpers `fetchJson`, `mutateJson` and `assertNoSecretsInBundle`; do not change those helpers.
```ts
{{FILE:apps/console/snippets/client_append.ts}}
```

### Step 3 — `apps/console/src/data/fixtures.ts`
(a) Change the import line `import type { ConsoleSnapshot } from '../api/types'` to:
```ts
import type { ConsoleSnapshot, OpsView } from '../api/types'
```
(b) Append at the very end of the file, exactly. **Do not** change `MOCK_SNAPSHOT`.
```ts
{{FILE:apps/console/snippets/fixtures_append.ts}}
```

### Step 4 — `apps/console/src/components/WorkerControls.tsx` (create, exactly)
```tsx
{{FILE:apps/console/src/components/WorkerControls.tsx}}
```

### Step 5 — `apps/console/src/components/OpsPanel.tsx` (create, exactly)
```tsx
{{FILE:apps/console/src/components/OpsPanel.tsx}}
```

### Step 6 — `apps/console/src/App.tsx` (four small edits; change nothing else)
1. After the line `import { GoalsPanel } from './components/GoalsPanel'` add:
   ```tsx
   import { OpsPanel } from './components/OpsPanel'
   ```
2. In `type Tab = …`, after the line `  | 'events'` add the line `  | 'ops'`.
3. In the `tabs` array, after `    { id: 'events', label: 'Events' },` add:
   ```tsx
       { id: 'ops', label: 'Ops' },
   ```
4. Find the **last** `      ) : null}` in the component, the one that closes the `tab === 'events'` block just before `    </div>`. After it, insert:
   ```tsx

         {tab === 'ops' ? (
           <OpsPanel
             mode={snap.mode}
             baseUrl={loadOpts.baseUrl}
             token={loadOpts.token}
             workers={snap.workers}
           />
         ) : null}
   ```

### Step 7 — `apps/console/src/ops.test.tsx` (create, exactly)
```tsx
{{FILE:apps/console/src/ops.test.tsx}}
```

### Step 8 — run
```bash
cd apps/console && npm ci && npm run lint && npm run test && npm run build && cd ../..
```
`apps/console/dist/` is git-ignored; do not commit it.

### Section-5 acceptance
- [ ] An **Ops** tab exists. Mock mode shows the `MOCK_OPS` events and queue and a "controls disabled" note.
- [ ] Live mode reads `/v1/ops/events` and `/v1/scheduler/queues`; a 404 on queues shows "Scheduler queues not available on this server"; fixture rows never appear in live mode.
- [ ] Drain and revoke POST to `/v1/workers/{id}/drain|revoke` with the bearer token; success shows `wk → <drain_state>`, and a 404 shows "… not available on this server".
- [ ] The existing `src/console.test.tsx` passes unchanged; lint shows no errors.
