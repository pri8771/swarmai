import type { ReactNode } from 'react'

export function Panel({
  title,
  subtitle,
  children,
  testId,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  testId?: string
}) {
  return (
    <section className="panel" data-testid={testId}>
      <header className="panel-head">
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  )
}
