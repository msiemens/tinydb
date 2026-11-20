# autose

Agent code for `.github/workflows/autose.yml`. Design: `architecture/`.

| File | Role |
| --- | --- |
| `llm.py` | Gemini REST client, function-calling loop, 8 tool rounds, 8192 output tokens, token log |
| `tools.py` | Per-role tools: analyst `list_dir read_file`; implementer adds `write_file` (not `tests/`, `.github/`, `autose/`, `.git`); tester `write_file` under `tests/` only; reviewer adds `run_tests` |
| `checks.py` | Script checks for stages 1, 2 and 6 |
| `stages.py` | analyst (1, 2), builder (3, 4, with the retry budget), reviewer (6) |
| `release.py` | Stage 5: push `autose/issue-<n>`, open the PR against `master`, wait for CI; post the review |
| `prompts/` | One prompt per role |
| `tests/` | Offline unit tests, no API calls: `python -m pytest autose/tests -o addopts=""` |

## Secrets and settings

- `GEMINI_API_KEY` (Actions secret). Only the analyst, builder and review jobs read it, and it is removed from the environment of every process that runs model-written code.
- `AUTOSE_PAT` (Actions secret, optional but needed for stage 5): a fine-grained token for this repository only, with Contents and Pull requests write. A pull request or push made with `GITHUB_TOKEN` does not start `ci-workflow.yml`, so without this token stage 5 stops with "no CI check started".
- Without `AUTOSE_PAT`, Settings > Actions > General > "Allow GitHub Actions to create and approve pull requests" must be on for `GITHUB_TOKEN` to open the pull request.

## Trigger

Add the label `autose` to an issue, or comment `/autose` on an issue (not a pull request). The actor needs `write` or `admin` on the repository.

## Known gaps

- Not yet run on Actions. Offline checks only: unit tests, and a scripted fake model driving the builder against the real TinyDB tests.
- The analyst prompt is a plain spec-writing prompt. Replace `prompts/analyst.md` Task 1 with your A1 skill.
- The reviewer's "behaviour I checked" is a prompt rule. The script only checks that the review names a file from the diff.
