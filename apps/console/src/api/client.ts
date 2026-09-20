/** Browser API client — never embeds provider secrets. */

import type { ConsoleSnapshot } from './types'
import { MOCK_SNAPSHOT } from '../data/fixtures'

const SECRET_RE = /(sk-[a-zA-Z0-9]+|api_key\s*=\s*\S+)/i

export function scrubSecrets(value: string): string {
  return value.replace(SECRET_RE, '[redacted]')
}

export function assertNoSecretsInBundle(payload: unknown): void {
  const blob = JSON.stringify(payload)
  if (SECRET_RE.test(blob)) {
    throw new Error('secret_material_detected_in_console_payload')
  }
}

export async function loadSnapshot(opts: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}): Promise<ConsoleSnapshot> {
  if (opts.mode === 'mock' || !opts.baseUrl) {
    const snap = structuredClone(MOCK_SNAPSHOT)
    assertNoSecretsInBundle(snap)
    return snap
  }
  // Live path: fetch real API; still scrub any accidental secret-shaped strings.
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const res = await fetch(`${opts.baseUrl}/v1/capacity`, { headers })
  if (!res.ok) {
    throw new Error(`api_error_${res.status}`)
  }
  const capacity = await res.json()
  assertNoSecretsInBundle(capacity)
  // Minimal live merge — console still labels unknown fields honestly.
  return {
    ...MOCK_SNAPSHOT,
    mode: 'live',
    mockVsLive: 'partial_live_capacity_remainder_fixture',
    capacity: (capacity.buckets ?? []).map(
      (b: { bucket_id: string; dimension: string; remaining: number | null; limit: number | null }) => ({
        bucketId: b.bucket_id,
        dimension: b.dimension,
        remaining: b.remaining,
        limit: b.limit,
      }),
    ),
  }
}
