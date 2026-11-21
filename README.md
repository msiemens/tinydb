# A3 AutoSE

Fork of TinyDB used for an agentic SDLC workflow that turns an issue into a tested, reviewed pull request. The repository holds the design (views, ADRs, a map of TinyDB), the workflow `.github/workflows/autose.yml`, and the agent code in `autose/`.

Library usage remains in [README.rst](README.rst).

Current progress and open items: [STATUS.md](STATUS.md).

## Repository

- Fork: https://github.com/Anilkumark17/tinydb
- Upstream: https://github.com/msiemens/tinydb
- Pinned commit: `edff96aeb2616402e9489d46e90a592c05565621` (`edff96a`)
- Tag: [`a3-pin`](https://github.com/Anilkumark17/tinydb/tree/a3-pin)
- Default branch: `master`. Pull requests from the workflow target `master`, because [ci-workflow.yml](.github/workflows/ci-workflow.yml) runs only for pull requests into `master`. `main` is protected as well and, at the pin, points at the same commit.
- Local checkout of the pin before this design commit: branch `main-pinned`

## Branch protection

`master` and `main` require a pull request. Administrators are included. Force pushes and deletions are off. A direct update was rejected with `422 Changes must be made through a pull request.` The workflow must not merge.

## Workflow permissions

The default `GITHUB_TOKEN` permission is read. Actions cannot approve pull requests. A job that pushes has to request `contents: write` itself. In the design, only the release job does.

## Model

Gemini, free tier. Secret name: `GEMINI_API_KEY`. Every role uses `gemini-3.5-flash-lite`. See [ADR-015](architecture/decisions/ADR-015.md).

Fallback: when Gemini stays overloaded or out of quota, the same call goes to `gemini-3.1-flash-lite`, then to Groq `openai/gpt-oss-120b` with at most 2048 output tokens. Secret name: `GROQ_API_KEY`. Without that secret there is no fallback. See [ADR-017](architecture/decisions/ADR-017.md) and [ADR-018](architecture/decisions/ADR-018.md).

Spend cap: the Gemini and Groq keys are on free tiers with no billing account linked, so no paid usage can occur and the effective cap is $0. A dollar cap can only be set in AI Studio once billing is enabled, and billing was never enabled.

The monthly spend cap is set in Google AI Studio under Spend → Monthly spend cap. An API key cannot set it.

## Issues

| Fork | Kind | File outside the fork | Issue |
| --- | --- | --- | --- |
| #1 | Bug | `issue1_bug_string_doc_ids.md` | [#1](https://github.com/Anilkumark17/tinydb/issues/1) |
| #2 | Bug | `issue2_bug_copy_between_dbs.md` | [#2](https://github.com/Anilkumark17/tinydb/issues/2) |
| #3 | Feature | `issue3_feature_document_in_doc_ids.md` | [#3](https://github.com/Anilkumark17/tinydb/issues/3) |
| #4 | Feature | `issue4_feature_search_limit.md` | [#4](https://github.com/Anilkumark17/tinydb/issues/4) |
| #5 | Vague | `issue5_vague_counting.md` | [#5](https://github.com/Anilkumark17/tinydb/issues/5) |

Issue texts and hidden tests are in this repository for grading. Model tools refuse to read `experiment/`.

```text
experiment/
  issues/          # the five issue texts
  hidden_tests/    # four tests per issue, not an agent input
architecture/
  views/
  decisions/
```

`results/`, `report.pdf`, `experiment/variants.md`, and `experiment/seeded_prs/` are in the repository. `demo.mp4` is not. `workflow/` holds a copy of the workflow and agents in the submission layout.

## Design

| View | Path |
| --- | --- |
| Components | [architecture/views/component.md](architecture/views/component.md) |
| Sequence for issue 1 | [architecture/views/sequence.md](architecture/views/sequence.md) |
| Stage map | [architecture/views/stage-map.md](architecture/views/stage-map.md) |
| ADRs 001-022 | [architecture/decisions/](architecture/decisions/) |
| TinyDB map the analyst reads | [ARCHITECTURE.md](ARCHITECTURE.md) |

## How to trigger

On an issue, add the label `autose`, or comment `/autose`. The actor needs write or admin on this repository. See [ADR-010](architecture/decisions/ADR-010.md). The workflow file is `.github/workflows/autose.yml`. A copy for the submission layout is under `workflow/`.

## Demo

The run to watch is issue #1, from the issue page to the posted review. There is no `demo.mp4` in this repository. Record that path, at most five minutes:

- Issue: https://github.com/Anilkumark17/tinydb/issues/1
- Run: https://github.com/Anilkumark17/tinydb/actions/runs/44799110233
- Pull request: https://github.com/Anilkumark17/tinydb/pull/19
- Review: https://github.com/Anilkumark17/tinydb/pull/19#issuecomment-7048813902

