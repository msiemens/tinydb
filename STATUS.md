# A3 status

Goal: an agentic SDLC workflow on a TinyDB fork that turns an issue into a tested, reviewed PR.

## Part 1: repo setup (done)

- Fork `Anilkumark17/tinydb`, pinned at `edff96a`. 228 upstream tests pass.
- Five issues on the fork:
  - #1: string `doc_ids` in `update`/`remove` (bug).
  - #2: `Document` in `doc_ids` (feature).
  - #3: copying between databases (bug).
  - #4: `search(limit=)` (feature).
  - #5: counting (vague).
- 20 hidden tests in `experiment/hidden_tests/`. 17 fail on the pinned code, as designed.
- Issue texts are in `experiment/issues/`. Their file numbers differ from the fork numbers for #2 and #3.

## Part 2: design (done, committed before any runner)

- Three views and ADR-001 to 010, committed as `ff62331`.
- Review fixed these gaps:
  - Component view: job count and per-agent tools.
  - Reviewer `run_tests` tool.
  - Labeler permission check.
- Added ADR-011 (token for release), ADR-012 (no secrets for model-written code) and ADR-013 (concurrency).

## Part 3: workflow and agents (built, not working end to end)

- `autose.yml` with eight jobs, plus the `autose/` Python agent code, prompts and offline tests.
- Offline testing only: 14 unit tests pass, and a scripted fake model drove the builder against the real suite (230 passed).
- First real runs:
  - Got through spec, design, code and tests.
  - Model ids changed twice: ADR-014, then ADR-015, `gemini-3.5-flash-lite` for all roles.
  - PR #12 opened, but CI failed, so the review never ran.
- Cause: `Python CI` is red on every run in the fork, including `master`, so a green-CI condition can never hold. The failing jobs are unconfirmed; the logs have not been read yet.
- Fix: stage 5 now fails only on a job newly red against `master`. Recorded as ADR-016, commit `768108b` on `a3-design`.
- Run 44784749664 passed gate and analyst, then the builder hit Gemini HTTP 503 (provider overload). ADR-017 adds a Groq fallback (`openai/gpt-oss-120b`, secret `GROQ_API_KEY`).
- Run 44787871458: Gemini 503 again; Groq returned 413 (free tier 8000 tokens per minute). ADR-018 tries `gemini-3.1-flash-lite` before Groq and caps Groq output at 2048 tokens.

## Incidents and limits

- ADR-014 was overwritten by mistake, then restored from git. The new decision was renumbered to ADR-016.
- `gh` is not installed in the build environment, so PR and secret steps are done in the browser.

## Decisions

- AI use stays disclosed in the README, as the course requires.
- Reviewer independence: the reviewer uses the same model as the builder. The report must state this.

## Next (browser)

1. Merge `a3-design` into `master` through a PR.
2. Close PR #12 and delete the `autose/issue-1` branch.
3. Check the `GEMINI_API_KEY` and `AUTOSE_PAT` secrets.
4. Comment `/autose` on issue #1 and collect the error lines of any red job.

## Still open

- Set the Gemini spend cap before further runs.
- `results/`, `variants.md` and the five seeded review PRs.
- Two decision experiments.
- The report, the demo and the roll-number file.
- Rewrite the ADRs in my own words, since the course requires them to be mine.
- Replace the sequence view with one from a real run.
