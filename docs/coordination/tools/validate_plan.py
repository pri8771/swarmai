#!/usr/bin/env python3
"""Read-only plan integrity/readiness validator; --render updates derived catalog only."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

COORD = Path(__file__).resolve().parents[1]
REPO = COORD.parents[1]
NAMES = ('V17_RECOVERY_PACKET_QUEUE.json', 'V17_TO_V23_PACKET_QUEUE.json',
         'FUTURE_EXECUTION_GRAPH_V18_TO_V30.json', 'ARTIFACT_REGISTRY.json')
SATISFIED = {'impl_complete', 'live_checkpointed', 'evidence_only', 'review_pending'}
SYNTHETIC = {'handoff','cross-version-verification','V1.7-live-integration',
             'V1.7-integrated-audit','V1.9-live','V2.3-live','V2.3-integrated-audit',
             'V2.3-integrated-evidence','V3-integrated-evidence'}
CONTRACT_ONLY = {'ART-V17-DURABLE-EFFECT-SCHEMA','ART-V20-INTEGRATION-CONTRACT'}


def deps(p):
    return p.get('depends', []) + p.get('depends_on', [])


def artifacts(p):
    return ([p['artifact']] if 'artifact' in p else []) + p.get('artifacts', []) + p.get('artifacts_also', [])


def completion_edges(p):
    # An aggregate's old implementation prerequisites are historical. Its
    # replacement children define completion, without child->parent cycles.
    if p.get('status') == 'split':
        return p.get('split_into', [])
    if p.get('status') in {'gaps_found','changes_required'}:
        return p.get('remediation', [])
    return deps(p)


def gate_satisfied(g):
    return g.get('status') in {'satisfied','closed','passed'} and bool(g.get('evidence_refs'))


def catalog(v23, future):
    packets = v23['packets'] + future.get('v30_packets', [])
    fingerprint = hashlib.sha256(json.dumps(packets,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    out = ['# Future execution packet catalog — V1.8 through V3.0', '',
           'Generated from the two planning packet JSON files by `tools/validate_plan.py --render`.',
           'Do not hand-edit packet cards. Proposed closure revision; not independent acceptance.',
           f'Packet contract digest: `{fingerprint}`', '',
           'Read only the active card, its referenced algorithm/contract and owned source. Shared rules:',
           '- One implementation session; one bounded concern per commit; source changes stay on the worker branch.',
           '- Listed paths marked new are proposed. Verify exact brownfield imports before implementation. Directory surfaces mean one bounded slice, not whole-directory rewrite.',
           '- If the slice needs more than three production files or lacks a frozen interface, split it during the final Fable sweep; later source surprises require a narrow amendment.',
           '- Routine code: Sonnet 4.6 medium effort. Transactions, security, scheduler and recovery: high effort plus independent diff review. Packaging: lower tier.',
           '- Run focused negative cases, Ruff and mypy; real DB/process tests for state boundaries. Record commands, exit codes and every skip. No product checks are claimed by this documentation generator.',
           '- Shared contracts: FUTURE_SCHEMA_CONTRACTS_V18_TO_V30_20260921.md, FUTURE_TRANSACTION_ALGORITHMS_V18_TO_V30_20260921.md and FUTURE_MIGRATION_SEQUENCE_V18_TO_V30_20260921.md. Packet JSON retains verification commands, owner and rollback fields; read that one object with this card.',
           '- Evidence: `docs/evidence/packets/<packet>/<run-id>/` with manifest, commands, redacted environment, receipts and summary; source SHA and evidence-commit SHA are separate.',
           '- Required identity: source/schema/lock/config/policy/route/manifest/protocol digests. Preserve all failed runs; never mint elapsed evidence or self-accept.',
           '- Rollback: disable the new path or restore the previous compatible snapshot; never erase unknown effects, lower generations or copy grants across projects.', '']
    for p in packets:
        d=deps(p)
        out += [f"## {p['id']}", '',
                f"Artifact(s): {', '.join(artifacts(p))}. SP{p.get('sp',2)}. Depends: {', '.join(d) or 'none'}. Type: {p.get('type','code')}.",
                f"Entry gates: {', '.join(p.get('entry_gates',[])) or 'none'}. Claim gates: {', '.join(p.get('exit_gates',[])) or 'none'}. Source state: {p.get('status','planned')}.", '',
                '**Owned surfaces:** ' + '; '.join(f'`{x}`' for x in p['surfaces']) + '.', '',
                '**Required behavior:** ' + p['behavior'], '',
                '**Negative cases:** ' + p['negative_tests'], '',
                '**Evidence and exit:** ' + p['exit_condition'], '']
    return '\n'.join(out)


def validate(v17, v23, future, registry, repo=None):
    errors=[]; warnings=[]; nodes={}; origin={}
    groups={'V17':v17['packets'],'V18-V23':v23['packets'],
            'FUTURE-coarse':future['packets'],'V30':future.get('v30_packets',[])}
    for group, packets in groups.items():
        for p in packets:
            pid=p.get('id')
            if not pid or pid in nodes:
                errors.append(f'duplicate/missing packet id: {pid}'); continue
            nodes[pid]=p; origin[pid]=group
    gates={}
    for doc in (v17,v23,future):
        for g in doc.get('gates',[]):
            if g['id'] in gates: errors.append(f"duplicate gate: {g['id']}")
            gates[g['id']]=g
            if g.get('status') in {'satisfied','closed','passed'} and not g.get('evidence_refs'):
                errors.append(f"gate lacks evidence: {g['id']}")
    for pid,p in nodes.items():
        for key,refs in [('depends',deps(p)),('split_into',p.get('split_into',[])),
                         ('remediation',p.get('remediation',[])),('basis',p.get('basis',[])),
                         ('maps_to',p.get('maps_to',[]))]:
            for ref in refs:
                if ref not in nodes: errors.append(f'{pid}: unresolved {key}: {ref}')
        if 'gate' in p: errors.append(f'{pid}: ambiguous legacy gate field')
        for ref in p.get('entry_gates',[])+p.get('exit_gates',[]):
            if ref not in gates: errors.append(f'{pid}: undefined gate {ref}')
        for claim, refs in p.get('claim_requirements',{}).items():
            if isinstance(refs,list):
                for ref in refs:
                    if ref not in nodes and ref not in gates: errors.append(f'{pid}: unknown claim input {claim}: {ref}')
        if p.get('status') in {'verified','accepted'}: errors.append(f'{pid}: worker queue carries acceptance')
        if p.get('status')=='split' and not p.get('split_into'): errors.append(f'{pid}: empty split')
        if p.get('status')=='gaps_found' and not p.get('remediation'): errors.append(f'{pid}: empty remediation')
        if origin[pid] in {'V18-V23','V30'}:
            for field in ('surfaces','behavior','negative_tests','evidence','exit_condition','verification','rollback','spec'):
                if not p.get(field): errors.append(f'{pid}: missing contract field {field}')
        if repo and p.get('spec'):
            path=p['spec'].split('#',1)[0]
            if not (repo/path).is_file(): errors.append(f'{pid}: missing spec {path}')
        for alias in p.get('aliases',[]):
            if alias in nodes and origin[alias]!='FUTURE-coarse': errors.append(f'{pid}: alias collides {alias}')
    vocab=set(v17.get('status_vocabulary',[]))
    for p in v17['packets']:
        if vocab and p.get('status') not in vocab: errors.append(f"{p['id']}: unknown status")
    # Check BOTH raw DAG and effective completion graph. Split/remediation edges
    # were not included by the prior validator despite its comment claiming so.
    for label,edge_fn in [('dependency',deps),('completion',completion_edges)]:
        state={}
        def visit(pid,trail):
            if state.get(pid)==2: return
            if state.get(pid)==1:
                errors.append(f'{label} cycle: '+ ' -> '.join(trail+[pid])); return
            state[pid]=1
            for ref in edge_fn(nodes[pid]):
                if ref in nodes: visit(ref,trail+[pid])
            state[pid]=2
        for pid in nodes: visit(pid,[])
    ids={a['artifact_id'] for a in registry['artifacts']}; covered=set()
    for pid,p in nodes.items():
        for art in artifacts(p):
            if art not in ids and art not in SYNTHETIC: errors.append(f'{pid}: unknown artifact {art}')
            covered.add(art)
    for a in registry['artifacts']:
        if a['target_version'] in {'1.7','1.8','1.9','2.0','2.3','3.0'} and a['artifact_id'] not in covered|CONTRACT_ONLY:
            errors.append('uncovered artifact: '+a['artifact_id'])
    mapped={ref for p in future['packets'] for ref in p.get('maps_to',[])}
    for p in v23['packets']+future.get('v30_packets',[]):
        if p['id'] not in mapped and p['id']!='18-00': errors.append('unmapped packet: '+p['id'])
    ready=[]; blocked={}
    def done(pid):
        p=nodes[pid]
        if p.get('status') in {'split','gaps_found','changes_required'}:
            children=completion_edges(p)
            return bool(children) and all(done(c) for c in children)
        return p.get('status') in SATISFIED
    if not errors:
        for p in v17['packets']:
            if p.get('status') not in {'planned','ready'}: continue
            if not all(done(d) for d in deps(p)): continue
            missing=[g for g in p.get('entry_gates',[]) if not gate_satisfied(gates[g])]
            if missing: blocked[p['id']]=missing
            else: ready.append(p['id'])
    return dict(ok=not errors,packet_counts={k:len(x) for k,x in groups.items()},
                gate_count=len(gates),registry_artifacts=len(ids),ready_v17=ready,
                entry_gate_blocked_v17=blocked,dispatch_authorized=False,
                activation=v17.get('activation',{}),errors=errors,warnings=warnings)


def main(argv):
    v17,v23,future,registry=[json.loads((COORD/name).read_text()) for name in NAMES]
    report=validate(v17,v23,future,registry,REPO)
    generated=catalog(v23,future)
    target=COORD/'FUTURE_PACKET_CATALOG_V18_TO_V30_20260921.md'
    if '--render' in argv and report['ok']:
        target.write_text(generated)
    elif not target.exists() or target.read_text()!=generated:
        report['errors'].append('derived packet catalog drift: run --render')
        report['ok']=False
    if '--json' in argv: print(json.dumps(report,indent=2))
    else:
        print('counts:',report['packet_counts'],'gates:',report['gate_count'])
        print('Candidate-ready after reviewed adoption:',', '.join(report['ready_v17']) or 'none')
        for e in report['errors']: print('ERROR',e)
        print('OK' if report['ok'] else 'FAILED')
        print('Readiness is not dispatch authorization or artifact acceptance.')
    return 0 if report['ok'] else 1

if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
