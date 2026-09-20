# Engineering self-development pack

Optional pack: the swarm proposes a tested improvement via isolated worktree,
sandbox tests, independent review, and a patch artifact. Never auto-merges or
deploys.

## Authority split

| Role | May |
|---|---|
| Runtime operator | Admit missions, approve merge manually |
| Code-generating worker | Edit allowlisted paths in isolated worktree only |
| Independent reviewer | Accept/reject patch; cannot be the patch author |

## Forbidden in generated diffs

- Approval / policy / release-rights expansion
- Secret handling changes that broaden access
- Main-branch writes or production deploy hooks
- Self-approval of merge

## Issue template

See `issues/sample-off-by-one.json`.
