# Decision-experiment variants

Two decisions were changed after a run failed, and the same issue was started again. The numbers below are the Actions runs in [results/runs.md](../results/runs.md). No other variant was run.

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
