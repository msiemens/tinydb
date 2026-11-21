# Reviewer check

The reviewer stage was run alone (`.github/workflows/review-check.yml`, ADR-022) on five seeded pull requests and on both heads of PR #22, once per model, with model fallback off. Each verdict is compared with the ground-truth label in [experiment/seeded_prs/LABELS.md](../experiment/seeded_prs/LABELS.md). Every row is in [reviewer_check.csv](reviewer_check.csv). Each review was also posted on its pull request.

Check runs: [44893677770](https://github.com/Anilkumark17/tinydb/actions/runs/44893677770) (gemini-3.5-flash-lite, Groq gpt-oss-120b) and [44894297904](https://github.com/Anilkumark17/tinydb/actions/runs/44894297904) (gemini-3.1-flash-lite).

## Targets

| Target | PR | Label | What is wrong |
| --- | --- | --- | --- |
| 01-string-ids | [#30](https://github.com/Anilkumark17/tinydb/pull/30) | approve | Nothing. Hidden tests for issue #1: 4/4. |
| 02-export-only | [#31](https://github.com/Anilkumark17/tinydb/pull/31) | code | Exports `Document`, copying unchanged. Hidden tests for issue #2: 0/4. Suite passes. |
| 03-truncated-table | [#32](https://github.com/Anilkumark17/tinydb/pull/32) | code | `tinydb/table.py` does not parse. |
| 04-count-drops-condition | [#33](https://github.com/Anilkumark17/tinydb/pull/33) | approach | `count(cond)` ignores `cond`. 32 suite tests fail. |
| 05-test-locks-the-bug | [#34](https://github.com/Anilkumark17/tinydb/pull/34) | code | New test asserts the issue #1 bug. Suite passes. |
| pr22-original | [#22](https://github.com/Anilkumark17/tinydb/pull/22), branch `evidence/pr22-original` | code | The workflow's first issue #2 patch. Hidden tests 0/4. |
| pr22-retry | [#22](https://github.com/Anilkumark17/tinydb/pull/22), branch `evidence/pr22-retry` | code | The workflow's second issue #2 patch. Hidden tests 0/4. |

## Results

| Model | Targets | Verdict equals label | Problems caught (of the bad PRs) | False approvals | Tokens |
| --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite (the workflow's reviewer) | 6 | 5 | 4 of 5 | 1 (pr22-original) | 72,335 |
| gemini-3.1-flash-lite | 7 | 3 | 3 of 6 | 3 (02-export-only, both PR #22 heads) | 383,997 |
| Groq openai/gpt-oss-120b | 6 | 0 | 0 of 5 | 0 | 31,467 |

"Caught" means a `code` or `approach` verdict on a PR whose label is not `approve`. gemini-3.1-flash-lite caught 04-count-drops-condition but called it `code`, not `approach`.

Groq returned no verdict on any target. Every call ended in HTTP 413: the free tier allows 8,000 tokens per minute and one review request was larger (for example 8,067 tokens on #30). This is a quota result, not a judgement of the model.

gemini-3.5-flash-lite on pr22-retry is not in the table because it was not run in a check run. In the AutoSE run that produced it ([44893468505](https://github.com/Anilkumark17/tinydb/actions/runs/44893468505)) the workflow's own reviewer approved it ([comment](https://github.com/Anilkumark17/tinydb/pull/22#issuecomment-7061206934)).

## What the reviewer caught and where it was wrong

- Both Gemini models caught the file that does not parse (03) and the test that locks in the bug (05).
- gemini-3.5-flash-lite labelled every seeded PR correctly, including the `approach` case (04).
- Every model that gave a verdict approved at least one patch for issue #2 that does not fix it. The suite passes on those patches, and the new tests check behaviour that already worked, so a reviewer that relies on `run_tests` sees green.
- gemini-3.1-flash-lite used about 4.5 times the tokens per review (54,857 against 12,056) and matched the label less often.
