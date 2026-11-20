# Sequence view

Planned sequence for a real issue, [tinydb#1](https://github.com/Anilkumark17/tinydb/issues/1) (`update()` / `remove()` with string doc ids). No Actions run exists yet. This is the path the workflow will take for that issue once the runner is built. The issue text and the failing checks below are already true on `edff96a`.

```mermaid
sequenceDiagram
  actor Maintainer
  participant Gate as gate
  participant Analyst as analyst flash
  participant Impl as implementer flash
  participant Tester as tester flash
  participant Py as pytest
  participant Rel as release script
  participant Rev as reviewer pro
  participant GH as GitHub

  Maintainer->>GH: add label autose on issue 1
  GH->>Gate: issues labeled
  Gate->>Gate: actor is OWNER, label is autose
  Gate->>Analyst: issue body as untrusted data, ARCHITECTURE.md
  Analyst->>GH: artifact spec.md
  Note over Analyst: script rejects the spec if a criterion has no observable result
  Analyst->>GH: artifact design.md
  Note over Analyst: script requires a path that exists and a function defined in that file
  Gate->>Impl: spec.md, design.md, branch autose/issue-1 from master
  Impl->>Impl: edit tinydb/table.py only through file tools
  Impl->>GH: artifact diff.patch
  Note over Impl: import tinydb must succeed before the tester starts
  Impl->>Tester: spec.md, design.md, diff. No implementer messages.
  Tester->>Tester: add tests under tests/ from the acceptance criteria
  Tester->>Py: uv run pytest
  alt pytest fails and the fix budget remains
    Py->>Impl: failing node ids and tracebacks only
    Impl->>Tester: new diff
    Tester->>Py: uv run pytest
  end
  Py->>Rel: test_report.md with exit code 0
  Rel->>GH: push autose/issue-1 and open a PR into master
  Rel->>GH: artifact pr.md with the PR url
  GH->>GH: ci-workflow.yml on the pull_request into master
  Rel->>Rev: issue 1 text, diff, checkout of the PR head
  Note over Rev: spec.md, design.md, and the builder transcript are not in this job
  Rev->>GH: artifact review.md
  alt verdict approve, or two rounds are used
    Rev->>Maintainer: PR left open
    Maintainer->>GH: merge or close
  else verdict code
    Rev->>Impl: review.md file list only, round 2
  else verdict approach
    Rev->>Analyst: review.md, round 2, then implement and test again
  end
```

On `edff96a`, `Table.update({'a': 2}, doc_ids=['1'])` returns `[]` and leaves the document unchanged, while `Table.get(doc_id='1')` returns the document. The sequence above is how issue 1 reaches a pull request. It is not a claim that a run has already done so.
