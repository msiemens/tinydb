"""Entry point: python -m autose <analyst|builder|review|release|post-review> ..."""
import argparse
import json
import os
import sys
import traceback

from . import llm, release, stages


def _out(path, key, value):
    """Write a step output for the next job."""
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(f"{key}={value}\n")


def _state(out, stage, result, detail=""):
    path = os.path.join(out, f"state-{stage}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"stage": stage, "result": result, "detail": detail}, fh)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autose")
    ap.add_argument("cmd", choices=["analyst", "builder", "review", "release", "post-review"])
    ap.add_argument("--work", default=".")
    ap.add_argument("--out", required=True)
    ap.add_argument("--issue-file")
    ap.add_argument("--issue-number", type=int)
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--start", choices=["analyst", "builder"], default="builder")
    ap.add_argument("--feedback-file")
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    os.environ["AUTOSE_USAGE"] = os.path.join(
        args.out, f"usage-{args.cmd}-r{args.round}.jsonl")
    issue = open(args.issue_file, encoding="utf-8").read() if args.issue_file else ""
    feedback = (open(args.feedback_file, encoding="utf-8").read()
                if args.feedback_file else "")
    try:
        if args.cmd == "analyst":
            stages.analyst(args.work, args.out, issue)
        elif args.cmd == "builder":
            stages.builder(args.work, args.out, args.issue_number, issue,
                           args.start, feedback)
        elif args.cmd == "review":
            verdict = stages.review(args.work, args.out, issue, args.round)
            _out(args.out, "verdict", verdict)
        elif args.cmd == "release":
            release.release(args.work, args.out, args.issue_number, args.round)
        elif args.cmd == "post-review":
            release.post_review(args.out, os.environ["PR_NUMBER"])
        _state(args.out, args.cmd, "pass")
        return 0
    except stages.StageFailed as exc:
        _state(args.out, args.cmd, "fail", exc.message)
        print(f"::error::{args.cmd} failed: {llm.redact(exc.message)} (see {exc.artifact})")
        return 1
    except Exception as exc:  # any other error stops the run (ADR-009)
        _state(args.out, args.cmd, "fail", f"{type(exc).__name__}")
        print(f"::error::{args.cmd} crashed: {type(exc).__name__}")
        print(llm.redact(traceback.format_exc()), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
