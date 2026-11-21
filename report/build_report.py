"""Build report.pdf with ReportLab. Run: python report/build_report.py"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

REPO = "https://github.com/Anilkumark17/tinydb"
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["BodyText"], fontName="Helvetica", fontSize=10,
                      leading=13.5, spaceAfter=5, alignment=TA_LEFT)
cell = ParagraphStyle("c", parent=body, fontSize=8.5, leading=10.5, spaceAfter=0)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=16,
                    spaceAfter=4)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
                    spaceBefore=8, spaceAfter=4)
small = ParagraphStyle("s", parent=body, fontSize=9, textColor=colors.HexColor("#444444"))


def P(text, style=body):
    return Paragraph(text, style)


def run(rid):
    return f'<link href="{REPO}/actions/runs/{rid}" color="blue">{rid}</link>'


def pr(n):
    return f'<link href="{REPO}/pull/{n}" color="blue">#{n}</link>'


def table(rows, widths, header=True):
    data = [[P(str(c), cell) for c in r] for r in rows]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")))
    t.setStyle(TableStyle(style))
    return t


s = []
s.append(P("Architecting an Agentic SDLC Workflow", h1))
s.append(P(f"Anilkumark17 / tinydb, pinned at <font face='Courier'>edff96a</font>. "
           f"Roll number 2025204018. Repository: <link href='{REPO}' color='blue'>{REPO}</link>",
           small))
s.append(P("The workflow is a fixed GitHub Actions pipeline. A person adds the label "
           "<font face='Courier'>autose</font>. An analyst writes spec.md and design.md, a builder "
           "edits the code and the tests, a script opens a pull request, and a separate reviewer "
           "posts a verdict. The workflow does not merge."))

s.append(P("1. Architecture", h2))
s.append(P("Four roles cover the six stages. The analyst does requirements and design in one "
           "process, because both are read-only and the design is a refinement of the spec. The "
           "implementer and the tester are different processes. The tester sees the spec, the "
           "design, and the diff, and does not see the implementer's messages. Release is a script: "
           "it pushes <font face='Courier'>autose/issue-N</font> and opens a pull request onto "
           "master. The reviewer is its own job. It sees the issue, the diff, and a fresh checkout. "
           "It can run the fixed pytest command. It has no token and cannot push."))
s.append(P("The controller is the workflow file, not a planner model. <font face='Courier'>"
           "autose.yml</font> has eight jobs: gate, analyst, builder, release, review, and, only "
           "after a code or approach verdict, rework, release_again and review_again. A job starts "
           "only after the previous check passes. Pytest failures retry inside the builder. A code "
           "verdict returns to the builder, and an approach verdict to the analyst, at most twice. "
           "On every finished issue the verdict was approve, so those edges were not taken. The "
           "sequence view is run " + run(44799110233) + ", issue #1, from the label to the review "
           "comment on pull request " + pr(19) + "."))
s.append(P("Stage checks are scripts, except the review verdict. spec.md needs testable criteria. "
           "design.md must name a file and a function that exist. The patch must import. pytest "
           "tests must exit 0. The pull request must be open. review.md must start with "
           "<font face='Courier'>verdict:</font> approve, code, or approach. Hand-offs are Actions "
           "artifacts. The branch holds only the code and the new tests, so the reviewer's checkout "
           "does not contain spec.md or design.md. Every file tool refuses experiment/, which is "
           "where the hidden tests live."))
s.append(P("Every model call goes to gemini-3.5-flash-lite first, then gemini-3.1-flash-lite, then "
           "Groq openai/gpt-oss-120b if the earlier ones stay overloaded. The usage log records which "
           "model answered. A second workflow, <font face='Courier'>review-check.yml</font>, runs "
           "only the reviewer on fixed pull requests with a chosen model and no fallback (ADR-022)."))

s.append(P("2. Design decisions", h2))
s.append(P("The full records are in architecture/decisions/. The three that mattered most are "
           "under the table."))
adr = [["ADR", "Chose", "Rejected", "Why", "Status"],
       ["001", "Analyst, implementer, tester, reviewer. Release is a script.", "One agent, or one agent per stage.", "The reviewer must be a separate process. Stages 1 and 2 share a read-only context.", "Accepted. Models superseded."],
       ["002", "Fixed Actions jobs and explicit back-edges.", "A planner model.", "The stage graph is known. A planner can skip the reviewer.", "Partly superseded by 011."],
       ["003", "Artifacts in, builder transcript out.", "Giving every role the full conversation.", "The tester and the reviewer would otherwise confirm the implementer.", "Accepted."],
       ["004", "Artifacts for state, the branch for code.", "Committing the spec onto the branch.", "A committed spec would be visible to the reviewer.", "Accepted."],
       ["005", "File tools for models, gh for release.", "A shell or GitHub MCP.", "An issue must not be able to name a command.", "Partly superseded by 012 and 021."],
       ["006", "Flash builds, Pro reviews.", "One model for every role.", "A stronger reviewer was the point of the split.", "Superseded by 014."],
       ["007", "Scripts and pytest decide. The reviewer decides only its verdict.", "An LLM judge for every stage.", "The model should not grade its own spec.", "Partly superseded by 011, 016, 019."],
       ["008", "Reviewer is its own job, prompt, and token.", "A prompt line that says do not push.", "Permissions hold the cut. A prompt does not.", "Job split held. The separate model did not."],
       ["009", "Budgets, timeouts, untrusted issue text.", "The six-hour Actions default.", "A tool loop would spend the quota.", "Tool rounds changed by 020."],
       ["010", "Label autose or /autose, from a writer. Base is master.", "Any comment, or a pull request onto main.", "CI runs only for pull requests into master.", "Partly superseded by 013."],
       ["011", "Release uses AUTOSE_PAT.", "GITHUB_TOKEN for the push.", "A token opened by GITHUB_TOKEN does not start CI.", "Accepted."],
       ["012", "Strip secrets. pytest tests only.", "pytest with no path.", "A bare pytest also collects the agent tests and the hidden tests.", "Accepted."],
       ["013", "Non-triggers get their own concurrency group.", "One group for every event.", "A stray comment would replace a queued run.", "Accepted."],
       ["014", "gemini-3.8-flash for every role.", "Staying on the 2.5 ids.", "The first run returned HTTP 404 for gemini-2.5-flash.", "Superseded by 015."],
       ["015", "gemini-3.5-flash-lite for every role.", "3.8-flash, and Pro.", "3.8-flash did not return. Pro has no free quota.", "Accepted. Extended by 017, 018."],
       ["016", "Fail stage 5 only on a new red check.", "Require the whole matrix to be green.", "Python CI was red on master.", "Accepted. Cause corrected by 019."],
       ["017", "Fall back to Groq when Gemini stays down.", "Stopping on the first 503.", "Run 44784749664 died on Gemini HTTP 503.", "Accepted."],
       ["018", "Try gemini-3.1-flash-lite before Groq. Cap Groq output.", "An uncapped Groq call.", "Groq returned 413 on the free tier.", "Accepted."],
       ["019", "CI collects only tests/. Wait only on pull-request checks.", "Blaming coveralls in advance.", "The red jobs were this repo's own test collection, including experiment/.", "Accepted."],
       ["020", "16 tool rounds.", "Staying at 8.", "Issue #2 stopped at BudgetExceeded.", "Accepted. Variant A."],
       ["021", "replace_in_file, and strip GROQ_API_KEY.", "Rewriting table.py with write_file.", "The write was cut off and the file did not parse.", "Accepted. Variant B."],
       ["022", "A reviewer-only workflow per model, fallback off.", "Reviewing seeded diffs through autose.yml.", "autose.yml reviews only branches it built.", "Accepted. Variant C."]]
s.append(table(adr, [1.0, 4.0, 3.4, 4.9, 3.3]))
s.append(Spacer(1, 6))
s.append(P("<b>Models (ADR-006, ADR-014, ADR-015).</b> The first design used a stronger model for "
           "the reviewer. gemini-2.5-flash returned HTTP 404. gemini-3.8-flash did not finish a "
           "free-tier call. gemini-3.1-pro-preview returned 429. Every role now calls "
           "gemini-3.5-flash-lite, with gemini-3.1-flash-lite and then Groq as fallbacks. The "
           "reviewer is still a separate job, but it is not a separate model. Pull request "
           + pr(22) + " is the cost of that."))
s.append(P("<b>What stage 5 measures (ADR-007, ADR-016, ADR-019).</b> Requiring a green Python CI "
           "matrix cannot pass on this fork while the matrix is red on master. The first guess, "
           "coveralls, was wrong. The confirmed cause was pytest collecting workflow/autose/tests "
           "and experiment/hidden_tests. The workflow now collects only tests/ and fails a pull "
           "request only for a check that is newly red."))
s.append(P("<b>Reviewer independence (ADR-008).</b> The job, the prompt, and the token are "
           "separate, and the reviewer does not see the builder transcript. That was not enough. "
           "The same model approved two patches that do not fix issue #2. Independence of process "
           "is not independence of judgement."))

s.append(P("3. Decision experiments", h2))
s.append(P("experiment/variants.md records three variants. A and B are one issue run twice with "
           "one knob changed. C runs the reviewer alone on fixed inputs, once per model."))
s.append(P("<b>A. Tool rounds, ADR-009 then ADR-020.</b> Issue #2, copying between databases. "
           "Run " + run(44887740431) + " stopped in the builder with BudgetExceeded at 8 tool rounds "
           "and opened no pull request. Run " + run(44888518600) + ", with the limit at 16, finished "
           "every stage and opened pull request " + pr(22) + ". The reviewer approved it. Hidden "
           "tests: 0/4, each <font face='Courier'>ValueError: Document with ID 1 already "
           "exists</font>. The patch only adds Document to __all__ and tests behaviour that already "
           "worked. A retry after ADR-021, run " + run(44893468505) + ", changed table.py (+4/-5), "
           "was approved again, and still passed 0/4. Raising the budget removed the stop. It did "
           "not produce a fix, and issue #2 is recorded as a known failure."))
s.append(P("<b>B. Edits, ADR-005 then ADR-021.</b> Issue #3, Document objects as doc ids. Run "
           + run(44889133139) + " rewrote tinydb/table.py with write_file. The output was cut off. "
           "The build check failed with <font face='Courier'>SyntaxError: unterminated "
           "triple-quoted string literal</font> at line 820. By the earlier rule the run stopped, "
           "with no retry. Run " + run(44889802429) + " gave the implementer replace_in_file. Every "
           "stage passed. Pull request " + pr(25) + " changes table.py by +16/-3. Hidden tests: "
           "4/4. The same change strips GROQ_API_KEY before model-written code runs."))
s.append(P("<b>C. Reviewer model, ADR-015 tested with ADR-022.</b> The five seeded diffs were "
           "opened as pull requests " + pr(30) + " to " + pr(34) + " and, with both heads of "
           + pr(22) + ", reviewed by each model with fallback off (check runs " + run(44893677770)
           + " and " + run(44894297904) + "). A verdict is caught when it is code or approach on a "
           "pull request whose label is not approve."))
s.append(table([["Reviewer model", "Verdict equals label", "Bad PRs caught", "False approvals", "Tokens"],
                ["gemini-3.5-flash-lite (the workflow's reviewer)", "5 of 6", "4 of 5", "1: PR #22 first head", "72,335"],
                ["gemini-3.1-flash-lite", "3 of 7", "3 of 6", "3: #31 and both PR #22 heads", "383,997"],
                ["Groq openai/gpt-oss-120b", "0 of 6", "0 of 5", "0 (no verdicts)", "31,467"]],
               [5.0, 2.6, 2.4, 4.4, 2.2]))
s.append(Spacer(1, 6))
s.append(P("Both Gemini models caught the file that does not parse (#32) and the test that locks in "
           "the bug (#34). The workflow's reviewer labelled every seeded pull request correctly, "
           "including the approach case (#33). Groq gave no verdict: every request ended in HTTP 413 "
           "on the free tier's 8,000 tokens per minute, which is a quota result, not a judgement of "
           "the model. gemini-3.1-flash-lite used about 4.5 times the tokens per review and was "
           "right less often. Every model that gave a verdict approved at least one issue #2 patch. "
           "Those patches pass the suite, so the reviewer's run_tests reports green."))

s.append(P("4. Results", h2))
s.append(P("Finished pull requests, from results/runs.md. Hidden tests were run against each "
           "pull-request branch, outside the workflow."))
s.append(table([["Issue", "Run", "PR", "Verdict", "Hidden", "Suite"],
                ["#1 string ids", run(44799110233), pr(19), "approve", "4/4", "231"],
                ["#2 copy", run(44893468505), pr(22), "approve", "0/4", "231"],
                ["#3 Document ids", run(44889802429), pr(25), "approve", "4/4", "232"],
                ["#4 search limit", run(44890273513), pr(26), "approve", "4/4", "231"],
                ["#5 count()", run(44890597042), pr(27), "approve", "4/4", "232"]],
               [3.2, 3.0, 1.6, 2.0, 1.8, 1.6]))
s.append(Spacer(1, 6))
s.append(P("On the pin, 3 of 20 hidden tests already passed. On the five final pull requests, 16 of "
           "20 pass. Issues #1, #3, #4, and #5 are fixed. Issue #2 is not. Every stage passed on the "
           "six runs that opened a pull request, including review. That rate is the workflow's own "
           "checks. It is not the hidden-test rate."))
s.append(P("<b>Failed runs.</b> Six runs stopped before review: three on Gemini 503 (the second and "
           "third then hit Groq 403 and Groq 413 in the fallback), one on a CI wait timeout caused by "
           "this repository's own test collection, one on BudgetExceeded, and one on a truncated "
           "file write. They led to ADR-017 to ADR-021. All runs are in "
           "results/results.csv."))
s.append(P("<b>Merge-readiness check.</b> The five questions used are the merge-readiness "
           "criteria in Hassan et al.: functional completeness, sound verification, hygiene, a "
           "readable rationale, and a frozen trail. Pull requests " + pr(19) + ", " + pr(25) + ", "
           + pr(26) + " and " + pr(27) + " meet them on the evidence available: hidden tests 4/4, "
           "new tests in the diff, a small table.py change, a pull-request body, and a linked "
           "Actions run. Linux and Windows CI were green; most macOS jobs were cancelled by GitHub, "
           "on master as well, so the matrix is not fully green. Pull request " + pr(22) + " fails "
           "functional completeness and is not merge-ready. None was merged by the workflow."))
s.append(P("<b>Tokens and spend.</b> 2,936,253 tokens in 393 model calls over the 14 runs listed "
           "in results/ (2,448,454 in AutoSE runs, 487,799 in the two reviewer checks), summed from "
           "each run's usage logs by usage-total.yml (run " + run(44895348926) + "; per run in "
           "results/usage.csv). Runs before PR #12 are not included. Both keys are on free tiers "
           "with no billing account, so no paid usage could occur and the effective spend cap is $0; "
           "a dollar cap cannot be set without billing."))

s.append(P("5. Hindsight", h2))
s.append(P("The first decision to change is the reviewer. A separate job with the same model "
           "approved both patches that do not fix issue #2, and the cheaper Gemini model did worse, "
           "not better. Changing the model is not enough on its own. The reviewer trusts green "
           "tests, and the builder's tests only cover what it changed. I would require the analyst's "
           "acceptance criteria to become tests that the tester writes before the implementer "
           "starts, and have the reviewer check each criterion against a named test. Issue #2's "
           "criteria describe copying between databases, and no test in either patch does that."))

s.append(P("6. Limitations and threats to validity", h2))
s.append(P("One repository and five issues. A pass rate here does not say how the same workflow "
           "behaves on a larger code base."))
s.append(P("The reviewer check has five seeded pull requests and two real ones. That is enough to "
           "show the failure mode and compare two models. It is not a measured false-approval rate."))
s.append(P("Hidden tests are outside the workflow, by design. Stage 4 can pass while those tests "
           "fail, as issue #2 did. The results depend on a person running them afterwards."))
s.append(P("Model availability changed the experiment. Overload on gemini-3.5-flash-lite sent some "
           "calls to gemini-3.1-flash-lite, and the usage log shows which; Groq could not be compared "
           "on its free tier."))
s.append(P("macOS runners were cancelled by GitHub on master as well. A green Linux job is not a "
           "green matrix, and the stage-5 rule treats those cancellations as already red on master."))
s.append(P("<b>AI use.</b> The ADRs, the views, the workflow, the agent code, the experiments and "
           "this report were drafted with coding agents (Cursor and Claude Code), as stated in the "
           "README. Every run id above opens on the public fork."))

doc = SimpleDocTemplate("report.pdf", pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="A3 AutoSE report",
                        author="2025204018")
doc.build(s)
