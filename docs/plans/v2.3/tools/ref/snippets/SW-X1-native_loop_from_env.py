def native_loop_from_env(
    tools: Mapping[str, ToolFn],
    *,
    grant: LiveGrant | None,
    env: Mapping[str, str] | None = None,
) -> tuple[BoundedNativeLoop | None, str]:
    """Build a live loop only with a base URL, a model and a usable LiveGrant.

    ``SPLITSIGNAL_MODEL`` falls back to ``DEFAULT_SPLITSIGNAL_MODEL``.

    ``SPLITSIGNAL_*`` (the SplitSignal consumer contract) wins over the legacy
    ``SWARM_ROUTER_*`` personal-router variables.
    """
    e = os.environ if env is None else env
    router: RouterClient
    ss_url = e.get("SPLITSIGNAL_BASE_URL", "").strip()
    if ss_url:
        model = e.get("SPLITSIGNAL_MODEL", "").strip() or DEFAULT_SPLITSIGNAL_MODEL
        router = SplitSignalClient(ss_url)
    else:
        base_url = e.get("SWARM_ROUTER_BASE_URL", "").strip()
        if not base_url:
            return None, "router_not_configured"
        model = e.get("SWARM_ROUTER_MODEL", "").strip()
        if not model:
            return None, "router_model_not_configured"
        router = RouterClient(base_url)
    pre = preflight_live_grant(grant, purpose="pursuit_native_loop", required_route=model)
    if not pre.ready:
        router.close()
        return None, pre.blocked_reason or "live_grant_not_ready"
    return BoundedNativeLoop(router, tools, model=model), "ready"
