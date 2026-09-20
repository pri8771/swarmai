# SwarmAI V0.9 Status — Release Hardening

**Date:** 2026-09-20  
**Branch:** `cursor/v0.9-release-hardening-11e2`  
**Interval commits:** IN FORCE

## Proof

```sh
uv run swarm release install-check   # ok
uv run swarm release harden          # ok — no tracked secrets
uv run swarm release verify          # passed
uv run swarm release demo-suite      # ok, cost_usd 0.0
```

Demo suite covered product journey, permission/approval, reliability matrix,
public contract, and mock parser demo.

## Packets

| Packet | Result |
|---|---|
| P62 Installability + packaging | complete — `install-check`, compose profiles, uv.lock |
| P63 Security + secret hardening | complete — git-tracked secret scan; local `.env` OK if ignored |
| P64 Documentation + examples | complete — user/security docs + `examples/v0_9/run_rc_demo.sh` |
| P65 Public demo + benchmark suite | complete — `release demo-suite` |
| P66 RC checkpoint | complete |

## Docs added

- `docs/user/GUIDE.md`
- `docs/user/ZERO_SPEND.md`
- `docs/user/TROUBLESHOOTING.md`
- `docs/security/HARDENING.md`

## Limitations

- Not a public launch
- Cloud live qualification still deferred
- OpenAI still payment-gated
