# Decision-experiment variants

Variants A and B changed a decision after a run failed and started the same issue again. Variant C is a planned comparison of reviewer models on fixed inputs. The runs are in [results/runs.md](../results/runs.md) and [results/reviewer_check.md](../results/reviewer_check.md).

## Variant A: tool rounds (ADR-009, then ADR-020)

What changed: `MAX_TOOL_ROUNDS` in the model loop, from 8 to 16. Nothing else in the prompt or the tools.

| | A0, ADR-009 | A1, ADR-020 |
| --- | --- | --- |
| Issue | #2, copying between databases | #2, same issue |
| Run | [44887740431](https://github.com/Anilkumark17/tinydb/actions/runs/44887740431) | [44888518600](https://github.com/Anilkumark17/tinydb/actions/runs/44888518600) |
| Stop | Builder, `BudgetExceeded` at 8 tool rounds | Every stage finished |
| Pull request | none | [#22](https://github.com/Anilkumark17/tinydb/pull/22), reviewer approved |
| Hidden tests | not run (no patch) | 0/4 pass |

The higher budget let the run finish. It did not make the patch correct. PR #22 adds `Document` to `__all__` and tests behaviour that already worked. The copy path is unchanged.

## Variant B: how the implementer edits a file (ADR-005, then ADR-021)

What changed: the implementer gained `replace_in_file` (exact text replacement) in addition to `write_file`. `GROQ_API_KEY` was added to the list of secrets stripped before model-written code runs. The tool-round limit stayed at 16.

| | B0, `write_file` only | B1, `replace_in_file` |
| --- | --- | --- |
| Issue | #3, `Document` objects as doc ids | #3, same issue |
| Run | [44889133139](https://github.com/Anilkumark17/tinydb/actions/runs/44889133139) | [44889802429](https://github.com/Anilkumark17/tinydb/actions/runs/44889802429) |
| Stop | Build check, `SyntaxError` at `tinydb/table.py` line 820. The model rewrote the whole file and the write was cut off. | Every stage finished |
| Pull request | none | [#25](https://github.com/Anilkumark17/tinydb/pull/25), reviewer approved |
| Hidden tests | not run (no patch) | 4/4 pass |

Rewriting an 850-line file in one tool call does not fit the output limit. Replacing a short span does. The second run is the one that fixed issue #3.

## Variant C: reviewer model (ADR-015, tested with ADR-022)

What changed: only the reviewer model. Same prompt, tools, verdict check and targets, fallback off. Targets: the five seeded PRs (#30 to #34) and the first head of PR #22 for every model, plus the second head of PR #22 for gemini-3.1-flash-lite.

| | C0, gemini-3.5-flash-lite (the workflow's reviewer) | C1, gemini-3.1-flash-lite | C2, Groq openai/gpt-oss-120b |
| --- | --- | --- | --- |
| Check run | [44893677770](https://github.com/Anilkumark17/tinydb/actions/runs/44893677770) | [44894297904](https://github.com/Anilkumark17/tinydb/actions/runs/44894297904) | [44893677770](https://github.com/Anilkumark17/tinydb/actions/runs/44893677770) |
| Verdict equals seeded label | 5 of 6 | 3 of 7 | 0 of 6 |
| Bad PRs caught | 4 of 5 | 3 of 6 | 0 of 5 |
| False approvals | 1 (PR #22 first head) | 3 (#31, both PR #22 heads) | 0 |
| Tokens | 72,335 | 383,997 | 31,467 |

C2 gave no verdict at all: every request ended in HTTP 413 on Groq's free tier (8,000 tokens per minute). C1 used about 4.5 times the tokens per review of C0 and was right less often. No model caught that the issue #2 patches leave copying unfixed. Those patches pass the suite, so the reviewer's `run_tests` reports green.
