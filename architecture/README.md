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
| [ADR-002](decisions/ADR-002.md) | Fixed Actions pipeline, explicit back-edges | Partly superseded by ADR-011 |
| [ADR-003](decisions/ADR-003.md) | Artifact hand-offs, reviewer sees only the issue and the diff | Accepted |
| [ADR-004](decisions/ADR-004.md) | Artifacts for run state, the branch for code only | Accepted |
| [ADR-005](decisions/ADR-005.md) | File tools and `gh`, scoped per job | Partly superseded by ADR-012 |
| [ADR-006](decisions/ADR-006.md) | Flash for building, Pro for review | Superseded by ADR-014 |
| [ADR-014](decisions/ADR-014.md) | Use `gemini-3.8-flash`; 2.5 ids are rejected | Superseded by ADR-015 |
| [ADR-015](decisions/ADR-015.md) | Free tier uses `gemini-3.5-flash-lite` | Accepted |
| [ADR-007](decisions/ADR-007.md) | Scripts and pytest decide, except the review verdict | Partly superseded by ADR-011 and ADR-016 |
| [ADR-008](decisions/ADR-008.md) | Reviewer job, prompt, model, and token are separate | Accepted |
| [ADR-009](decisions/ADR-009.md) | Budgets, timeouts, and untrusted issue text | Accepted |
| [ADR-010](decisions/ADR-010.md) | Label or `/autose` from a writer, one run per issue | Partly superseded by ADR-013 |
| [ADR-011](decisions/ADR-011.md) | Release uses a repository-scoped token so CI starts | Accepted |
| [ADR-012](decisions/ADR-012.md) | Model-written code runs without secrets; test command is `uv run pytest tests` | Accepted |
| [ADR-013](decisions/ADR-013.md) | Non-trigger events get their own concurrency group | Accepted |
| [ADR-016](decisions/ADR-016.md) | Stage 5 fails on a CI regression, not on a CI already red on master | Accepted |
| [ADR-017](decisions/ADR-017.md) | Fall back to Groq when Gemini stays unavailable | Accepted |
| [ADR-018](decisions/ADR-018.md) | Try `gemini-3.1-flash-lite` before Groq, and cap Groq output | Accepted |
| [ADR-019](decisions/ADR-019.md) | CI collects only `tests/`, and release waits only on pull-request checks | Accepted |
| [ADR-020](decisions/ADR-020.md) | Raise the tool-round limit from 8 to 16 | Accepted |
| [ADR-021](decisions/ADR-021.md) | Edit files by exact replacement, and strip the Groq key | Accepted |

TinyDB itself is described in [`ARCHITECTURE.md`](../ARCHITECTURE.md) at the repository root. The workflow opens pull requests against `master`, because `.github/workflows/ci-workflow.yml` runs only for pull requests into `master`. The sequence view is [run 44799110233](https://github.com/Anilkumark17/tinydb/actions/runs/44799110233).
