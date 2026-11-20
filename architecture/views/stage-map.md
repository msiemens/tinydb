# Stage map

| Stage | Agent | What it is given | Artifact | Check | Final pass or fail |
| --- | --- | --- | --- | --- | --- |
| 1 Requirements | analyst, `gemini-3.5-flash-lite` | Issue title and body, wrapped as data. `ARCHITECTURE.md`. Read-only tree. | `spec.md` | Every acceptance criterion names an action and an observable result. | Python script. The model does not grade its own spec. |
| 2 Design | analyst, same process as stage 1, after stage 1 passes | `spec.md` plus the tree. | `design.md` | At least one repository path that exists on disk, and at least one function name defined in that file. | Python script, using the tree at `edff96a` or the default-branch tip. |
| 3 Implementation | implementer, `gemini-3.5-flash-lite`, new process | `spec.md`, `design.md`, write access to source files. No shell. | `diff.patch` | `uv run python -c "import tinydb"` exits 0. | The process exit code. |
| 4 Testing | tester, `gemini-3.5-flash-lite`, new process | `spec.md`, `design.md`, the diff. Not the implementer's messages. Writes only under `tests/`. | `test_report.md` | `uv run pytest` exits 0, including tests that already existed. | The pytest exit code. |
| 5 Release | release script, no model | Branch name, `spec.md` title, passing `test_report.md`. | `pr.md` and the PR url | PR state is `OPEN` and its base is `master`. The `ci-workflow` run for that SHA completes with success. | `gh` and the Checks API. |
| 6 Review | reviewer, `gemini-3.5-flash-lite`, new process | Issue text, the diff, checkout of the PR head. No builder transcript, no `spec.md`, no `design.md`. | `review.md` | First line is `verdict: approve`, `verdict: code`, or `verdict: approach`. A non-approve verdict names a file. At most two rounds. | The reviewer chooses the verdict. The script only checks that the line is one of the three and that the round counter is at most 2. |

A failed check is written into that stage's artifact and the run stops, except where a back-edge is still inside its budget:

| From | To | Budget |
| --- | --- | --- |
| Stage 4, pytest failed | Stage 3 | 2 retries, then 1 return to stage 2, then stop |
| Stage 6, `verdict: code` | Stage 3, then 4, then 5, then 6 | 2 review rounds in total |
| Stage 6, `verdict: approach` | Stage 2, then 3, 4, 5, 6 | 2 review rounds in total |
| Stage 6, `verdict: approve`, or round 2 finished | Maintainer | The workflow does not merge |

The human's decision is not a seventh agent stage. The pull request stays open.
