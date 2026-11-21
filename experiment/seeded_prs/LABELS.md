# Reviewer-check diffs

Five diffs a reviewer can be shown, with the ground-truth label the workflow's verdict line uses: `approve`, `code`, or `approach`.

These diffs were not opened as pull requests and were not sent to the reviewer. The reviews that did run are the five workflow pull requests in [results/runs.md](../../results/runs.md). Diff 02 is the shape of pull request #22, which the reviewer approved and which the hidden tests reject.

| File | Label | Why that label |
| --- | --- | --- |
| [01-string-ids.diff](01-string-ids.diff) | approve | Converts string doc ids with `document_id_class` before `update` and `remove` look them up. That is the issue #1 behaviour. |
| [02-export-only.diff](02-export-only.diff) | code | Adds `Document` to `__all__` and does not change copying. The issue is not fixed. |
| [03-truncated-table.diff](03-truncated-table.diff) | code | Cuts `table.py` off in the middle of `_update_table`. The file does not parse. |
| [04-count-drops-condition.diff](04-count-drops-condition.diff) | approach | `count(cond)` stops using `cond` and returns the table length. That breaks a call the issue does not ask to change. |
| [05-test-locks-the-bug.diff](05-test-locks-the-bug.diff) | code | The new test asserts that `update` with a string id returns `[]` and leaves the document. It records the bug as the expected result. |
