# Architecture

Design for the AutoSE workflow. These files were committed before any agent runner. Decisions are in `decisions/`. Views are in `views/`.

| View | File |
| --- | --- |
| Components, tools, and calls | [views/component.md](views/component.md) |
| Sequence for issue 1 | [views/sequence.md](views/sequence.md) |
| Stage, agent, artifact, check | [views/stage-map.md](views/stage-map.md) |

| ADR | Decision | Status |
| --- | --- | --- |
| [ADR-001](decisions/ADR-001.md) | Three model roles plus a release script | Accepted |
| [ADR-002](decisions/ADR-002.md) | Fixed Actions pipeline, explicit back-edges | Accepted |
| [ADR-003](decisions/ADR-003.md) | Artifact hand-offs, reviewer sees only the issue and the diff | Accepted |
| [ADR-004](decisions/ADR-004.md) | Artifacts for run state, the branch for code only | Accepted |
| [ADR-005](decisions/ADR-005.md) | File tools and `gh`, scoped per job | Accepted |
| [ADR-006](decisions/ADR-006.md) | Flash for building, Pro for review | Accepted |
| [ADR-007](decisions/ADR-007.md) | Scripts and pytest decide, except the review verdict | Accepted |
| [ADR-008](decisions/ADR-008.md) | Reviewer job, prompt, model, and token are separate | Accepted |
| [ADR-009](decisions/ADR-009.md) | Budgets, timeouts, and untrusted issue text | Accepted |
| [ADR-010](decisions/ADR-010.md) | Label or `/autose` from a writer, one run per issue | Accepted |

TinyDB itself is described in [`ARCHITECTURE.md`](../ARCHITECTURE.md) at the repository root. The workflow, when it exists, opens pull requests against `master`, because `.github/workflows/ci-workflow.yml` runs only for pull requests into `master`.
