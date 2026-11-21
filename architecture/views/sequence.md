# Sequence view

This is the path of [Actions run 44799110233](https://github.com/Anilkumark17/tinydb/actions/runs/44799110233) on [issue #1](https://github.com/Anilkumark17/tinydb/issues/1). It opened [pull request #19](https://github.com/Anilkumark17/tinydb/pull/19) and posted [the review](https://github.com/Anilkumark17/tinydb/pull/19#issuecomment-7048813902). The verdict was `approve`. No rework job ran.

Every model call in this run used `gemini-3.5-flash-lite`. The reviewer was not a different model. Times are the job times recorded for this run.

```mermaid
sequenceDiagram
  actor Maintainer
  participant Gate as gate 9s
  participant Analyst as analyst 22s
  participant Builder as builder 1m23s
  participant Rel as release 25m43s
  participant Rev as reviewer 21s
  participant GH as GitHub

  Maintainer->>GH: label autose on issue 1
  GH->>Gate: issues labeled
  Gate->>Gate: actor is the owner, label is autose
  Gate->>Analyst: issue body as untrusted data, ARCHITECTURE.md
  Analyst->>GH: spec.md passes the script
  Analyst->>GH: design.md names a file and a function that exist
  Analyst->>Builder: spec.md and design.md
  Builder->>Builder: implementer edits tinydb/table.py
  Builder->>Builder: import tinydb exits 0
  Builder->>Builder: tester writes tests/test_autose_issue_1.py
  Builder->>Builder: uv run pytest tests exits 0
  Note over Builder: no pytest retry and no return to design
  Builder->>Rel: diff.patch and test_report.md
  Rel->>GH: push autose/issue-1 and open PR 19 onto master
  Rel->>GH: wait while Python CI runs
  Note over Rel: Linux and Windows green. macOS jobs cancelled by GitHub, on master as well
  Rel->>Rev: issue text, diff, checkout of the PR head
  Note over Rev: no spec.md, no design.md, no builder transcript, no token
  Rev->>GH: review.md verdict approve, posted as a PR comment
  Rev->>Maintainer: pull request left open
```

The back-edges in the stage map (pytest retry, return to design, `verdict: code`, `verdict: approach`) were not taken on this run. They were also not taken on the finished runs for issues #3, #4, and #5. Issue #2's finished run took this same shape and the reviewer approved a patch that does not fix the bug. That run is [44888518600](https://github.com/Anilkumark17/tinydb/actions/runs/44888518600).
