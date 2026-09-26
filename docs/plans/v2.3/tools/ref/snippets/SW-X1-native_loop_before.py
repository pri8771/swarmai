def native_loop_from_env(
    tools: Mapping[str, ToolFn],
    *,
    grant: LiveGrant | None,
    env: Mapping[str, str] | None = None,
) -> tuple[BoundedNativeLoop | None, str]:
    """Build a live loop only with a router URL, a model and a usable LiveGrant."""
    e = os.environ if env is None else env
    base_url = e.get("SWARM_ROUTER_BASE_URL", "").strip()
    if not base_url:
        return None, "router_not_configured"
    model = e.get("SWARM_ROUTER_MODEL", "").strip()
    if not model:
        return None, "router_model_not_configured"
    pre = preflight_live_grant(grant, purpose="pursuit_native_loop", required_route=model)
    if not pre.ready:
        return None, pre.blocked_reason or "live_grant_not_ready"
    return BoundedNativeLoop(RouterClient(base_url), tools, model=model), "ready"
