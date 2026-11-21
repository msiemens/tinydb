# Component view

`autose.yml` has eight Actions jobs: `gate`, `analyst`, `builder`, `release`, `review`, then, only after a `code` or `approach` verdict, `rework`, `release_again` and `review_again` for the second round (ADR-002). The analyst, builder, review, rework and review_again jobs call a model. The gate and both release jobs do not. Arrows are artifact hand-offs, not a shared conversation.

Every model call goes to `gemini-3.5-flash-lite` first. If it stays overloaded or out of quota, the call goes to `gemini-3.1-flash-lite`, then to Groq `openai/gpt-oss-120b` (ADR-017, ADR-018). The usage log records which model answered.

A separate workflow, `review-check.yml`, runs only the reviewer on fixed pull requests with a chosen model and no fallback (ADR-022). `usage-total.yml` adds up the usage logs of listed runs.

```mermaid
flowchart TD
  maintainer["Maintainer: label autose or comment /autose"]
  gate["gate job\nno model\nchecks the actor"]
  analyst["analyst job\ngemini-3.5-flash-lite\ntools: list_dir, read_file"]
  builder["builder job, rework job\nno shared token with the reviewer"]
  implementer["implementer process\ngemini-3.5-flash-lite\ntools: list_dir, read_file, write_file, replace_in_file\nno shell, no push"]
  tester["tester process\ngemini-3.5-flash-lite\ntools: list_dir, read_file, write_file under tests/ only\nno implementer transcript"]
  pytest["pytest\nworkflow step, not a model tool"]
  release["release job, release_again job\nscript only, no model\ntools: git push, gh pr create\ncontents write, pull-requests write"]
  reviewer["review job, review_again job\ngemini-3.5-flash-lite\ntools: list_dir, read_file, run_tests\nfresh checkout of the PR head\nno token in the model process"]
  post["post step\nscript posts review.md"]
  human["Maintainer merges or closes"]

  maintainer --> gate --> analyst
  analyst -->|"spec.md then design.md"| builder
  builder --> implementer -->|"diff.patch"| tester
  tester --> pytest
  pytest -->|"fail, under budget"| implementer
  pytest -->|"pass"| release
  release -->|"pr.md and open PR"| reviewer
  reviewer --> post --> human
  post -->|"verdict code, round under 2"| implementer
  post -->|"verdict approach, round under 2"| analyst
```

The analyst reads `ARCHITECTURE.md`, the issue text, and the tree. It cannot push.

The builder job runs two processes one after the other. The tester process is a new Gemini call. Its prompt contains `spec.md`, `design.md`, the diff, and later the pytest log. It does not contain the implementer's messages. The job's `GITHUB_TOKEN` can read the repository. Only the release job can push, and only that job has `pull-requests: write`.

The reviewer process has no `GITHUB_TOKEN` and no git credentials. A script that runs after it posts `review.md`. The model can read the checkout and call `run_tests`, which runs the fixed pytest command and takes no arguments. The model cannot push.

Nothing in this diagram merges the pull request.
