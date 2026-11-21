# AutoSE runs

| Issue | Run | PR | Review | Verdict | Hidden tests | Upstream suite |
| --- | --- | --- | --- | --- | --- | --- |
| #1 | [44799110233](https://github.com/Anilkumark17/tinydb/actions/runs/44799110233) | [#19](https://github.com/Anilkumark17/tinydb/pull/19) | [comment](https://github.com/Anilkumark17/tinydb/pull/19#issuecomment-7048813902) | approve | 4/4 pass | 231 passed (228 + 3 new) |
| #2 | [44887740431](https://github.com/Anilkumark17/tinydb/actions/runs/44887740431) | none | none | n/a | n/a | n/a |
| #2 | [44888518600](https://github.com/Anilkumark17/tinydb/actions/runs/44888518600) | [#22](https://github.com/Anilkumark17/tinydb/pull/22) | [comment](https://github.com/Anilkumark17/tinydb/pull/22#issuecomment-7060476290) | approve | 0/4 pass | 231 passed |
| #2 | [44893468505](https://github.com/Anilkumark17/tinydb/actions/runs/44893468505) | [#22](https://github.com/Anilkumark17/tinydb/pull/22) (force-pushed) | [comment](https://github.com/Anilkumark17/tinydb/pull/22#issuecomment-7061206934) | approve | 0/4 pass | 231 passed |
| #3 | [44889133139](https://github.com/Anilkumark17/tinydb/actions/runs/44889133139) | none | none | n/a | n/a | n/a |
| #3 | [44889802429](https://github.com/Anilkumark17/tinydb/actions/runs/44889802429) | [#25](https://github.com/Anilkumark17/tinydb/pull/25) | [comment](https://github.com/Anilkumark17/tinydb/pull/25#issuecomment-7060664003) | approve | 4/4 pass | 232 passed |
| #4 | [44890273513](https://github.com/Anilkumark17/tinydb/actions/runs/44890273513) | [#26](https://github.com/Anilkumark17/tinydb/pull/26) | [comment](https://github.com/Anilkumark17/tinydb/pull/26#issuecomment-7060711541) | approve | 4/4 pass | 231 passed |
| #5 | [44890597042](https://github.com/Anilkumark17/tinydb/actions/runs/44890597042) | [#27](https://github.com/Anilkumark17/tinydb/pull/27) | [comment](https://github.com/Anilkumark17/tinydb/pull/27#issuecomment-7060755024) | approve | 4/4 pass | 232 passed |

## Issue #1 notes

- Stages: gate 9s, analyst 22s, builder 1m23s, release 25m43s (mostly waiting on CI), review 21s. Rework not needed.
- PR #19 changes `tinydb/table.py` (+5 -5) and adds `tests/test_autose_issue_1.py` (+32).
- Earlier attempts on issue #1 failed outside the agents: Gemini 503 (runs 44784749664, 44786814645, 44787871458; ADR-017, ADR-018) and a CI timeout caused by the repository's own test collection (run 44790059127; ADR-019).
- Python CI: Linux and Windows green. Most macOS jobs are cancelled by GitHub ("not acquired by Runner ... after multiple attempts"), on `master` as well.

## Issue #2 notes

- Fork issue #2 is the copying bug (copying documents between databases).
- Two `/autose` comments (06:25 and 14:26) started no run, and neither did opening and merging PR #20, though a `git push` did. Adding the `autose` label started the run.
- Run 44887740431: gate and analyst passed. In the builder, Gemini 3.5 lite returned 503, 3.1 lite took over, and the implementer stopped at the 8-round tool limit (`BudgetExceeded`). ADR-020 raises the limit to 16.
- Run 44888518600 (16 rounds): every stage passed. PR #22 only adds `Document` to `__all__` in `tinydb/__init__.py` and adds tests of behaviour that already worked. The copy path in `tinydb/table.py` is unchanged.
- Hidden tests `experiment/hidden_tests/test_issue2.py`: 0/4 pass, each with `ValueError: Document with ID 1 already exists`.
- The reviewer approved with "Findings: None." This is a false approval by a reviewer on the same model as the builder.

- Retry, run 44893468505 (with `replace_in_file`): every stage passed. The new head of PR #22 changes `tinydb/table.py` (+4 -5) and adds tests. Hidden tests still 0/4, and the reviewer approved again. The first head is kept on branch `evidence/pr22-original`, the second on `evidence/pr22-retry`.

## Issue #3 notes

- Fork issue #3: allow passing `Document` objects to `update()`/`remove()`.
- Run 44889133139: gate and analyst passed. The builder's build check failed with `SyntaxError: unterminated triple-quoted string literal` at `tinydb/table.py` line 820. The implementer rewrote the 854-line file with `write_file`, and the output was cut off. By design the run stops without retry (ADR-007). ADR-021 adds `replace_in_file`.
- The same fix adds `GROQ_API_KEY` to the secrets removed before model-written code runs.
- Run 44889802429 (with `replace_in_file`): every stage passed. PR #25 changes `tinydb/table.py` (+16 -3) and adds tests. Hidden tests 4/4.

## Issue #4 notes

- Fork issue #4: `search(limit=)`. Run 44890273513: every stage passed on the first try. PR #26 changes `tinydb/table.py` (+22 -16) and adds tests. Hidden tests 4/4.

## Issue #5 notes

- Fork issue #5: the vague counting issue. Run 44890597042: every stage passed on the first try. PR #27 makes `Table.count()` accept no condition and return `len(self)` (`tinydb/table.py` +4 -2). Hidden tests 4/4.

## Summary

- Final outcome per issue: #1, #3, #4 and #5 fixed (hidden tests 4/4 each). #2 not fixed after two runs (0/4 both times), approved by the reviewer both times. Known failure.
- Total hidden tests on the final PRs: 16/20 pass. On the pinned code, 3/20 pass.
- Reviewer in the workflow: 6 approvals, 2 false approvals (both #2 runs). No rework round was triggered on any run. Seeded reviewer checks: [reviewer_check.md](reviewer_check.md).
- Tokens: 2,936,253 in 393 model calls over the 14 runs listed in `results/` (2,448,454 in AutoSE runs, 487,799 in the two reviewer checks). Per run and model: [usage.csv](usage.csv), summed from each run's `usage-*.jsonl` artifacts by `usage-total.yml` (run [44895348926](https://github.com/Anilkumark17/tinydb/actions/runs/44895348926)). Earlier runs from before PR #12 are not included.
- Hidden test results were checked locally against each PR branch, outside the workflow (ADR-003).
