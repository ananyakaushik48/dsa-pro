#!/usr/bin/env python3
"""
scaffold_project.py — Generate planning artifact stubs into a project directory.

Walks you through (or accepts as flags) a minimal discovery brief, then writes
empty-but-templated files for the rest of the planning workflow so you can
fill them in conversationally with Claude. Mirrors the templates in
references/templates.md and the workflow in references/project-planning.md.

USAGE
    python scripts/scaffold_project.py [OPTIONS]

OPTIONS
    --name NAME           Project name (will be used in titles and the directory name).
    --out PATH            Output directory (default: ./project/<name>).
    --sdlc SDLC           One of: lean | scrum | kanban | devops | tdd | waterfall | ddd | mixed.
                          See references/sdlc.md for guidance.
    --owner NAME          Project owner / DRI.
    --regulated           Add regulated-domain artifacts (traceability matrix, risk
                          management file). Implies --sdlc waterfall unless overridden.
    --interactive         Prompt for missing fields instead of using placeholders.
    --force               Overwrite existing files in the output dir.

EXAMPLES
    python scripts/scaffold_project.py --name medbook --sdlc waterfall --regulated
    python scripts/scaffold_project.py --name notebookd --sdlc lean --interactive

The script never invokes a network or third-party tool — it writes plain
markdown files you can edit, commit, and iterate on.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    p.add_argument("--name", default=None, help="Project name.")
    p.add_argument("--out", default=None, help="Output directory.")
    p.add_argument(
        "--sdlc",
        choices=["lean", "scrum", "kanban", "devops", "tdd", "waterfall", "ddd", "mixed"],
        default=None,
        help="SDLC choice (see references/sdlc.md).",
    )
    p.add_argument("--owner", default=None, help="Project owner / DRI.")
    p.add_argument(
        "--regulated",
        action="store_true",
        help="Add regulated-domain artifacts.",
    )
    p.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for missing fields instead of placeholders.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files in the output dir.",
    )
    return p.parse_args(argv)


def prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val or (default or "")


def resolve(args: argparse.Namespace) -> dict[str, str | bool]:
    name = args.name
    if not name and args.interactive:
        name = prompt("Project name")
    if not name:
        name = "untitled-project"
    name = slugify(name)

    sdlc = args.sdlc
    if not sdlc and args.interactive:
        sdlc = prompt(
            "SDLC (lean / scrum / kanban / devops / tdd / waterfall / ddd / mixed)",
            default="mixed",
        )
    if not sdlc:
        sdlc = "waterfall" if args.regulated else "mixed"

    owner = args.owner
    if not owner and args.interactive:
        owner = prompt("Owner / DRI", default="<owner>")
    if not owner:
        owner = "<owner>"

    out = args.out or f"./project/{name}"

    return {
        "name": name,
        "sdlc": sdlc,
        "owner": owner,
        "out": out,
        "regulated": bool(args.regulated),
        "force": bool(args.force),
    }


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled-project"


# ---------------------------------------------------------------------------
# File writers (return content; the main loop writes to disk)
# ---------------------------------------------------------------------------


def today() -> str:
    return datetime.date.today().isoformat()


def discovery_brief(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Discovery Brief: {ctx['name']}

        **Date.** {today()}
        **Owner.** {ctx['owner']}
        **Status.** Discovery

        ## Problem
        <One paragraph. What problem, for whom, and what happens today when they hit it.>

        ## Users
        <Who they are, how many, how often they hit the problem, what they do instead today.>

        ## Success measure
        <The single number that says we won. Include the time horizon.>

        ## Constraints
        - Compliance / regulatory: <none | HIPAA | PCI | FDA Class II | ...>
        - Latency / scale: <P99 < N ms at K QPS | offline OK | ...>
        - Budget / runway: <$X / N months / N engineers>
        - Team: <who, what languages and stacks>
        - Hard deadline: <date or none>
        - Soft deadline: <date or none>

        ## Adjacent systems
        <What this connects to (DBs, queues, identity, billing, other services) and where the seams are.>

        ## What can we ship if we cut everything cuttable?
        <The honest MVP.>

        ## Unknowns
        - <Unknown 1, with plan to resolve (spike, prototype, customer interview, ...)>
        - <Unknown 2 ...>

        ## Decision
        <Build / don't build / spike further. If build → SDLC choice (recorded in ADR-0001).>
        """
    )


def prd(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # PRD: {ctx['name']}

        **Status.** Draft
        **Owner.** {ctx['owner']}
        **Engineering lead.** <name>
        **Designer.** <name | n/a>

        ## Problem and users
        <2–4 sentences. The user, the problem, the impact.>

        ## Goals
        - <Goal 1, measurable.>
        - <Goal 2, measurable.>

        ## Non-goals
        - <Explicit cuts. "We are not solving X.">

        ## Success metrics
        - Primary: <single number; threshold; how measured>
        - Secondary: <leading indicator(s)>
        - Counter-metric: <what we'd notice if we hurt something we care about>

        ## User stories
        - As a <user>, I want <ability> so that <outcome>.
        - ...

        ## Functional requirements

        | ID | Requirement | Priority |
        | --- | --- | --- |
        | FR-001 | <statement> | Must |
        | FR-002 | <statement> | Should |
        | FR-003 | <statement> | Could |

        ## Non-functional requirements

        | ID | Requirement | Threshold |
        | --- | --- | --- |
        | NFR-001 | P99 latency under expected load | < 100 ms |
        | NFR-002 | Availability | 99.9% |
        | NFR-003 | Data retention | <as required by compliance> |

        ## Out of scope
        <What this PRD explicitly does not cover.>

        ## Open questions
        - <Q1>
        - <Q2>

        ## Appendix: alternatives considered (briefly)
        - <Alt 1>: <why not>
        - <Alt 2>: <why not>
        """
    )


def adr_0001_sdlc(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # ADR-0001: SDLC choice — {ctx['sdlc']}

        **Date.** {today()}
        **Status.** Proposed
        **Deciders.** {ctx['owner']}

        ## Context and problem statement
        <Background. What forces are at play. Constraints from the discovery brief.>

        ## Decision drivers
        - <Driver 1>
        - <Driver 2>

        ## Considered options
        1. **{ctx['sdlc']}** (this decision)
        2. <Alternative SDLC>
        3. <Alternative SDLC>

        See [`references/sdlc.md`](../../references/sdlc.md) for the playbooks behind each.

        ## Decision
        We chose **{ctx['sdlc']}**. <One paragraph on why this matches the risk shape of the project.>

        ## Consequences
        - Positive: <...>
        - Negative: <...>
        - What this constrains downstream: <cadence, ceremony, artifacts required>

        ## Links
        - Discovery brief: `discovery-brief.md`
        - PRD: `prd.md`
        """
    )


def adr_template(n: int) -> str:
    return textwrap.dedent(
        f"""\
        # ADR-{n:04d}: <title in present tense>

        **Date.** {today()}
        **Status.** Proposed

        ## Context
        <2–4 sentences. What forces are at play.>

        ## Decision
        <What we chose, in one sentence.>

        ## Consequences
        - Positive: <...>
        - Negative: <...>
        - Neutral: <...>
        """
    )


def wbs(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # WBS: {ctx['name']}

        ## Milestone 1 — <demo-able outcome> (target: week N)
        **Risks retired this milestone.** <list>
        **Modules touched.** <list of module names>

        - [ ] WBS-1.1 — <ticket title> — owner: <name> — size: S/M/L/XL
        - [ ] WBS-1.2 — <ticket title> — owner: <name> — size: S/M/L/XL
        - [ ] WBS-1.3 — <ticket title> — owner: <name> — size: S/M/L/XL

        ## Milestone 2 — <demo-able outcome> (target: week M)
        ...

        ## Cross-cutting work
        - [ ] WBS-CC.1 — observability dashboards
        - [ ] WBS-CC.2 — load test harness
        - [ ] WBS-CC.3 — runbook
        """
    )


def risk_register(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Risk Register: {ctx['name']}

        | ID | Risk | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation | Owner | Trigger to act | Status |
        | --- | --- | --- | --- | --- | --- | --- | --- |
        | R-001 | <description> | M | H | <mitigation> | <owner> | <measurable trigger> | Open |
        | R-002 | <description> | L | M | <mitigation> | <owner> | <measurable trigger> | Open |

        Review cadence: <weekly | per gate | per milestone>.
        """
    )


def verification_plan(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Verification Plan: {ctx['name']}

        ## Invariants (per module)
        - <Module A → invariant statement>
        - <Module B → invariant statement>

        ## Test layers

        | Layer | Framework | Coverage of invariants | Where |
        | --- | --- | --- | --- |
        | Unit | <pytest / cargo test / vitest> | Examples per branch | `tests/unit/` |
        | Property | <hypothesis / fast-check / proptest> | Oracle pattern | `tests/property/` |
        | Integration | <pytest / playwright / ...> | Cross-module behavior | `tests/integration/` |
        | Fuzz | <atheris / libFuzzer / ...> | Random byte inputs | `fuzz/` |
        | Bench | <criterion / pytest-benchmark / tinybench> | Perf regressions per access pattern | `bench/` |

        See [`references/verification.md`](../../references/verification.md) for the discipline behind each.

        ## Microbench discipline
        - Workloads benched: sequential, random, zipfian.
        - Warmup iterations: <N>.
        - Sample count: <M>.
        - Hardware target: <CPU, RAM, allocator, OS>.
        - Regression threshold: ±<X>%.

        ## CI gating
        - Unit + property + integration: blocking on PR.
        - Fuzz: nightly, alerts on new crash.
        - Bench: nightly, alerts on >X% regression.
        """
    )


def definition_of_done(ctx: dict) -> str:
    # SDLC-flavored: tweak items based on the picked methodology.
    extras = []
    if ctx["sdlc"] == "tdd":
        extras.append("- [ ] Tests authored *before* implementation (Red/Green/Refactor cycle)")
        extras.append("- [ ] Property test (oracle pattern) for every non-trivial DSA")
    if ctx["sdlc"] in ("scrum", "kanban", "devops", "mixed"):
        extras.append("- [ ] Feature flag rolled out (if applicable) or removed")
    if ctx["sdlc"] in ("waterfall",) or ctx["regulated"]:
        extras.append("- [ ] SDS updated; traceability matrix row populated")
        extras.append("- [ ] V&V protocol executed; results filed")
        extras.append("- [ ] Risk file updated for the changed area")
    if ctx["sdlc"] == "ddd":
        extras.append("- [ ] Aggregate invariants checked at the seam")
        extras.append("- [ ] Context map updated if the change affects a boundary")
    if ctx["sdlc"] == "lean":
        extras.append("- [ ] Hypothesis result documented in the learning log")

    extras_block = "\n".join(extras) if extras else "<no SDLC-specific extras>"

    return textwrap.dedent(
        f"""\
        # Definition of Done: {ctx['name']}

        A story is "Done" when:

        - [ ] Code merged to trunk
        - [ ] All tests (unit + property + integration) pass in CI
        - [ ] If touching a non-trivial DSA: invariant function + property test (oracle pattern) + microbench in CI
        - [ ] PR reviewed and approved by at least one other engineer
        - [ ] Docs updated (README / runbook / API doc as applicable)
        - [ ] Observability hooked up: metrics + logs at the right verbosity
        - [ ] Deployed to staging and exercised
        - [ ] No new TODO without a tracked ticket

        ## SDLC-specific ({ctx['sdlc']})
        {extras_block}
        """
    )


def context_map(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Context Map: {ctx['name']}

        ## Contexts
        - **<Context A>.** <what it owns>
        - **<Context B>.** <what it owns>
        - **<Context C>.** <what it owns>

        ## Relationships

        | Upstream | Downstream | Relationship | Translation |
        | --- | --- | --- | --- |
        | <A> | <B> | <Customer/Supplier \\| Shared Kernel \\| ACL \\| Conformist> | <how the model translates at the seam> |

        ## Ubiquitous language disambiguation
        - "<Term>": in <context A> = <meaning>; in <context B> = <meaning>.
        """
    )


def traceability_matrix(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Traceability Matrix: {ctx['name']}

        | Req ID | Requirement | Design ref | Code ref | Verification ref | V&V outcome | Status |
        | --- | --- | --- | --- | --- | --- | --- |
        | FR-001 | <statement> | SDS §x.y | src/<path> | test/<path> | <PASS / FAIL / pending> | Open / Closed |
        | FR-002 | <statement> | SDS §x.y | src/<path> | test/<path> | <PASS / FAIL / pending> | Open / Closed |
        | NFR-001 | <statement> | SDS §x.y | infra/<path> | V&V protocol VV-NN | <PASS / FAIL / pending> | Open / Closed |

        Every requirement must have all non-status cells filled before release.
        """
    )


def risk_management_file(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Risk Management File (ISO 14971-style): {ctx['name']}

        ## Hazard inventory

        | ID | Hazard | Hazardous situation | Harm | Severity (1–5) | Probability (1–5) | Risk score | Mitigation | Residual risk | Verified by |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | H-001 | <description> | <when it occurs> | <patient/user harm> | <1–5> | <1–5> | <S×P> | <controls> | <post-mitigation S> | <test ref> |

        Mitigations themselves can introduce new hazards (control of control); rerun the analysis for the post-mitigation state.
        """
    )


def module_spec_template(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # Module: <name>

        **Owner.** <name | "any">
        **Layer.** Domain | Application | Adapter | Infrastructure

        ## Responsibility
        <One sentence.>

        ## Public interface
        - `op_one(arg) -> result` — query / command. Invariant: <...>.
        - `op_two(arg) -> result` — query / command. Invariant: <...>.

        ## Invariants at the seam
        - <statement>

        ## Depends on
        - <other module>
        - <external system, via which adapter>

        ## Internal DSA picks (if non-trivial)
        - <structure> + fallback <fallback> + trap <trap>. (See [`references/decision-tree.md`](../../../references/decision-tree.md).)

        ## Verification
        See `../verification-plan.md`.
        """
    )


def project_readme(ctx: dict) -> str:
    return textwrap.dedent(
        f"""\
        # {ctx['name']}

        Planning workspace for **{ctx['name']}**. Generated by `scripts/scaffold_project.py` on {today()}.

        ## Files

        - `discovery-brief.md` — problem, users, success measure, constraints.
        - `prd.md` — what we're building and why.
        - `decisions/ADR-0001-sdlc-choice.md` — SDLC choice (this project: **{ctx['sdlc']}**).
        - `decisions/ADR-NNNN-*.md` — append-only architecture decisions.
        - `wbs.md` — milestones → tickets, with T-shirt sizes.
        - `risk-register.md` — known risks with triggers + mitigations.
        - `verification-plan.md` — test layers, microbench discipline, CI gating.
        - `definition-of-done.md` — what "shipped" means for this project.
        - `context-map.md` — bounded contexts + seams (DDD).
        - `modules/<name>.md` — per-module specs (5–10 lines each).
        {"- `traceability-matrix.md` — regulated: requirement → code → test → V&V." if ctx['regulated'] else ""}
        {"- `risk-management-file.md` — regulated: ISO 14971-style hazard inventory." if ctx['regulated'] else ""}

        ## Workflow

        Open `discovery-brief.md` first. Fill it in with Claude conversationally — see
        the workflow in [`references/project-planning.md`](../../references/project-planning.md).
        Decisions worth recording go in `decisions/` as new ADRs (copy ADR-0001 as a template).

        The artifacts are *tools the team uses*, not deliverables to file. Keep them lean
        enough to re-read.

        SDLC: **{ctx['sdlc']}**. See the playbook in [`references/sdlc.md`](../../references/sdlc.md).
        """
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def write_file(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        print(f"  SKIP  {path} (exists; pass --force to overwrite)")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  WRITE {path}")
    return True


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ctx = resolve(args)

    out = Path(ctx["out"]).resolve()
    if out.exists() and not ctx["force"] and any(out.iterdir()):
        print(f"Output directory {out} is not empty.")
        print("Pass --force to write into it anyway (existing files won't be touched without --force).")
    out.mkdir(parents=True, exist_ok=True)

    print(f"\nScaffolding project '{ctx['name']}' into {out}")
    print(f"  SDLC: {ctx['sdlc']}")
    print(f"  Owner: {ctx['owner']}")
    print(f"  Regulated: {ctx['regulated']}\n")

    files: list[tuple[Path, str]] = [
        (out / "README.md", project_readme(ctx)),
        (out / "discovery-brief.md", discovery_brief(ctx)),
        (out / "prd.md", prd(ctx)),
        (out / "decisions" / "ADR-0001-sdlc-choice.md", adr_0001_sdlc(ctx)),
        (out / "decisions" / "ADR-0002-template.md", adr_template(2)),
        (out / "wbs.md", wbs(ctx)),
        (out / "risk-register.md", risk_register(ctx)),
        (out / "verification-plan.md", verification_plan(ctx)),
        (out / "definition-of-done.md", definition_of_done(ctx)),
        (out / "context-map.md", context_map(ctx)),
        (out / "modules" / "module-template.md", module_spec_template(ctx)),
    ]

    if ctx["regulated"]:
        files.append((out / "traceability-matrix.md", traceability_matrix(ctx)))
        files.append((out / "risk-management-file.md", risk_management_file(ctx)))

    written = 0
    for path, content in files:
        if write_file(path, content, ctx["force"]):
            written += 1

    print(f"\nDone. {written}/{len(files)} files written.\n")
    print("Next steps:")
    print(f"  1. Open {out / 'discovery-brief.md'} and fill it in (conversationally with Claude).")
    print(f"  2. Refine the PRD and the SDLC ADR once discovery is solid.")
    print(f"  3. As decisions come up, add them as ADRs in {out / 'decisions'}.")
    print(f"  4. Per-module DSA picks belong in {out / 'modules'} files, one per module.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
