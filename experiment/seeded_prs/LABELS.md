# Reviewer-check diffs

Five diffs a reviewer can be shown, with the ground-truth label the workflow's verdict line uses: `approve`, `code`, or `approach`.

Each diff was opened as a pull request (#30 to #34) and reviewed by the reviewer stage alone, per model, through `.github/workflows/review-check.yml` (ADR-022). Results: [results/reviewer_check.md](../../results/reviewer_check.md). Diff 02 is the shape of pull request #22, which the reviewer approved and which the hidden tests reject.

| File | Label | Why that label |
| --- | --- | --- |
| [01-string-ids.diff](01-string-ids.diff), PR #30 | approve | Converts string doc ids with `document_id_class` before `update` and `remove` look them up. That is the issue #1 behaviour. |
| [02-export-only.diff](02-export-only.diff), PR #31 | code | Adds `Document` to `__all__` and does not change copying. The issue is not fixed. |
| [03-truncated-table.diff](03-truncated-table.diff), PR #32 | code | Opens a triple-quoted string inside `_update_table`, so the rest of `table.py` is cut off and the file does not parse. |
| [04-count-drops-condition.diff](04-count-drops-condition.diff), PR #33 | approach | `count(cond)` stops using `cond` and returns the table length. That breaks a call the issue does not ask to change. |
| [05-test-locks-the-bug.diff](05-test-locks-the-bug.diff), PR #34 | code | The new test asserts that `update` with a string id returns `[]` and leaves the document. It records the bug as the expected result. |
