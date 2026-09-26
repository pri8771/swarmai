@router.get("/ops/events")
async def list_ops_events(
    request: Request,
    project_id: str | None = None,
    principal: Principal = Depends(get_principal),
    auth: AuthRegistry = Depends(get_auth),
) -> dict[str, Any]:
    from swarm.observability import OpsEventLog

    log = getattr(request.app.state, "ops_events", None)
    if log is None:
        log = OpsEventLog()
        request.app.state.ops_events = log
    if project_id:
        auth.require_project(principal, project_id)
        return {"events": log.list_events(project_id=project_id)}
    if "admin" in principal.roles:
        return {"events": log.list_events()}
    # Non-admin without project_id: only the principal's projects; never unscoped events.
    events: list[dict[str, Any]] = []
    for pid in sorted(principal.project_ids):
        events.extend(log.list_events(project_id=pid))
    events.sort(key=lambda e: (str(e.get("at")), str(e.get("event_id"))))
    return {"events": events[-100:]}
