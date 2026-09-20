import type { Availability, ProfileState } from '../api/types'

const AVAIL_LABEL: Record<Availability, string> = {
  available: 'available',
  unknown: 'unknown',
  retired: 'retired',
  disabled: 'disabled',
  gated: 'gated',
  exhausted: 'exhausted',
}

export function StatusBadge({
  kind,
  value,
}: {
  kind: 'availability' | 'profile' | 'generic'
  value: string
}) {
  const tone =
    value === 'available' || value === 'qualified' || value === 'online'
      ? 'ok'
      : value === 'unknown' || value === 'provisional' || value === 'waiting'
        ? 'warn'
        : value === 'retired' || value === 'exhausted' || value === 'quarantine' || value === 'blocked'
          ? 'bad'
          : 'muted'
  const label =
    kind === 'availability'
      ? AVAIL_LABEL[value as Availability] ?? value
      : kind === 'profile'
        ? (value as ProfileState)
        : value
  return (
    <span className={`badge badge-${tone}`} data-testid={`badge-${value}`}>
      {label}
    </span>
  )
}
