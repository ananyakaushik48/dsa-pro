# SDLC Playbook

Six software development lifecycle traditions. Each section: **one-line pitch**, **when to reach for it**, **when not to**, **cadence and ceremony**, **artifacts**, **how it lands on dsa-pro's verification discipline**, **anti-patterns**.

The right SDLC is a function of the *risk shape* of the project, not of fashion. A regulated medical-device pipeline picked because the founders "like moving fast" ships once and never again. A startup MVP picked with stage gates ships nothing in 18 months. Match the process to the failure mode you most fear.

## Contents

1. [Decision table: which SDLC to pick](#decision-table-which-sdlc-to-pick)
2. [Agile (Scrum / Kanban / iterative)](#agile-scrum--kanban--iterative)
3. [Lean / MVP / discovery-driven](#lean--mvp--discovery-driven)
4. [DevOps / CI-CD / trunk-based](#devops--ci-cd--trunk-based)
5. [TDD + property-test-first](#tdd--property-test-first)
6. [Waterfall / phased (regulated)](#waterfall--phased-regulated)
7. [DDD / hexagonal / clean architecture](#ddd--hexagonal--clean-architecture)
8. [Combining traditions](#combining-traditions)
9. [How SDLC choice changes dsa-pro's workflow](#how-sdlc-choice-changes-dsa-pros-workflow)

---

## Decision table: which SDLC to pick

| Signal in the project | Default SDLC | Why |
| --- | --- | --- |
| Regulated domain (FDA, HIPAA, PCI, ISO 26262, SOX) | **Waterfall / phased + DDD seams** | Audit trail and traceability matrix are the deliverable; rework cost is high. |
| Early-stage product, "what should we even build" | **Lean + Kanban** | Discovery beats throughput; flow over cadence. |
| Mature product, known scope, multiple teams | **Agile (Scrum) + DevOps** | Predictable cadence + automated delivery. |
| Platform / infra / API where bugs are downstream debt | **TDD + trunk-based + DDD** | Correctness work pays for itself; type-safe boundaries. |
| Algorithm-heavy / data-structure-heavy module | **TDD with property-tests + oracle pattern** | Invariants are the spec; property tests catch what examples miss. See [`verification.md`](verification.md). |
| Complex domain (insurance, logistics, settlement) | **DDD + Scrum (or Kanban for ops teams)** | Bounded contexts contain the complexity; ubiquitous language carries it. |
| Single dev, single product, fast iteration | **Lean + trunk-based, skip ceremony** | Process overhead has nowhere to amortize. |
| Brownfield refactor or migration | **Strangler-fig + DevOps + ADRs** | Replace incrementally behind a seam; each ADR a step. |
| Hardware-in-the-loop / embedded with long flash cycles | **Phased + extensive sim/HIL** | Real cycles are slow; pay for the simulator. |
| Research / exploratory ML / one-off | **Notebook + minimal SDLC** | Don't force a process onto throwaway code. |

When in doubt: start Lean + trunk-based + ADRs for hard decisions, and *upgrade* the process when the project graduates from one risk shape to another. Process drag is real, but unprincipled process *and* the absence of process both cost more than picking a default and tightening it later.

---

## Agile (Scrum / Kanban / iterative)

**Pitch.** Time-boxed cycles produce small, working increments that you can inspect and adapt. Scrum is calendar-driven (sprints); Kanban is flow-driven (WIP-limited).

**When to reach for it.** Stable team, known general scope, frequent stakeholder feedback available, work that decomposes into < 1-2 week stories.

**When not to.** Pure research; regulated phase-gated work; solo dev (Scrum ceremony is overhead); when "the team" is actually 1.5 people.

**Cadence and ceremony.**

- **Scrum.** 1–2 week sprints. Backlog refinement, sprint planning, daily standup (≤ 15 min), sprint review, retrospective. Definition of Ready for stories entering the sprint; Definition of Done for stories leaving it.
- **Kanban.** WIP limits per column ("In Progress" ≤ N), cycle time and throughput as the metric; no sprints. Replenishment meeting on demand.

**Artifacts.** Backlog, sprint goal, burndown / cumulative flow, retro action items, Definition of Done. See [`templates.md`](templates.md) → *Sprint plan*, *Definition of Done*.

**How it lands on dsa-pro.** Each story that touches a non-trivial data structure adds an entry to the story's DoD: "invariants documented, property test passes, microbench in CI." The decision-tree pick is one tag on the story; the trap is another. *Reviews* are the moment to catch a too-clever picked structure or a missing fallback.

**Anti-patterns.**

- Story-point theater. Estimates that don't predict reality are noise — switch to T-shirt sizes or cycle-time tracking.
- Process worship. The retro must produce changes; if it produces only commiseration, it's broken.
- Velocity as a KPI. Encourages padded estimates. Use throughput / cycle time instead.
- "Mini-waterfall" sprints — designing for two sprints, then building, then testing. Each story stands alone.

---

## Lean / MVP / discovery-driven

**Pitch.** Build the smallest thing that lets you learn whether the bigger thing is worth building. Treat assumptions as hypotheses; pick the assumption that, if wrong, kills the project, and test that one first.

**When to reach for it.** Pre-product-market-fit; new market; internal tool nobody asked for yet; greenfield where the requirement is "you'll know it when you see it."

**When not to.** Known scope and known users (e.g., "rewrite the billing engine to match the regulator's new spec" — that's not discoverable, it's a spec).

**Cadence.** Build–Measure–Learn loops, with the loop length scaled to the question. A landing page A/B test is a day; a pricing experiment is two weeks; a market segment test is two months. The loop is the unit of work.

**Artifacts.**

- **Riskiest-assumption test (RAT)** — what's the assumption that, if wrong, kills this idea, and what's the cheapest experiment that lets you find out.
- **One-page lean canvas** instead of a full PRD (replace with PRD when scope hardens).
- **Learning log** — what we believed, what we tested, what we learned, what we'll do next. Out-of-date learning logs are a leading indicator of theater.

**How it lands on dsa-pro.** Lean pulls hard *against* premature data-structure complexity. The first version uses `Map` and `List` and a linear scan; you upgrade only when measurement (not theorizing) shows a bottleneck. Decision-tree picks come *later*, when the workload stabilizes and the access pattern is empirically known, not guessed. dsa-pro's "stdlib first" principle is most powerful in this phase.

**Anti-patterns.**

- **"MVP" that's actually V1 with corners cut.** A minimum *viable* product still has a viable customer outcome. Cutting features without cutting the goal produces a non-viable product, not an MVP.
- Treating "ship and see" as the entire methodology. Without a hypothesis, "see" produces nothing measurable.
- Lean *forever*. At some point the product graduates and needs durable engineering. Notice the moment.

---

## DevOps / CI-CD / trunk-based

**Pitch.** Treat delivery as engineering. Every change goes through the same automated pipeline; merges to trunk are continuous; production deploys are routine. Recover fast rather than try not to fail.

**When to reach for it.** Any system that runs in production for users. Modern web, mobile, API, infra. Mostly mandatory in 2026; the question is only how much of it you adopt.

**When not to.** Air-gapped, regulated-firmware contexts may need to *also* satisfy phased traceability — the answer there is "DevOps + audit," not "no DevOps."

**Cadence and ceremony.**

- **Trunk-based development.** Short-lived branches (≤ 24 h), small PRs, behind feature flags. No long-lived feature branches.
- **CI.** Every push runs unit + property + integration + lint + security scan + dependency check + microbench (where stable). Pipeline < 10 min as a hard goal — past that, devs route around it.
- **CD.** Merge to trunk auto-deploys to a staging environment; deploy to prod is one click (or fully automated with canary + auto-rollback).
- **Observability.** Logs, metrics, traces, error budgets, SLOs. Failed deploys auto-rollback; canary release for risky changes.

**Artifacts.** `.github/workflows/*` (or equivalent), Dockerfile, deployment manifests, observability dashboards, runbook, SLOs / error budgets, incident postmortems (blameless). See [`templates.md`](templates.md) → *Postmortem*.

**How it lands on dsa-pro.** The property tests + microbenches from [`verification.md`](verification.md) live *in CI*, not in a manual harness. Regressions get caught before merge. Benchmarks that wobble are pinned to a fixed hardware profile or marked non-blocking. Trap-laden picks (e.g., Robin Hood with a load factor near capacity) get a guard test that fails when invariants drift.

**Anti-patterns.**

- **Branch-per-feature for weeks.** Defeats the whole point. Use flags.
- **Pipeline > 30 minutes.** Devs will work around it. Cache aggressively; parallelize; trim.
- **Tests in CI but no SLO in prod.** You have correctness signal and no reliability signal — you're flying half-blind.
- **Feature flag debt.** Every flag added is a deletion ticket. Audit quarterly.

---

## TDD + property-test-first

**Pitch.** Tests first — but make property tests, not just example tests, the workhorse. The test is the spec; the implementation passes it. Combined with the oracle pattern from [`verification.md`](verification.md), this is the highest-correctness mode of working.

**When to reach for it.** Algorithm-heavy code (parsers, schedulers, allocators, data structures, distributed protocols). Anywhere a wrong answer is worse than a slow one. Compiler / serializer work. Anywhere with a *trivially correct reference* available.

**When not to.** UI tweaks, exploratory ML, throwaway scripts. Tests-first there is theater.

**Cadence.**

- **Red.** Write a failing test (example or property).
- **Green.** Write the smallest code that makes it pass.
- **Refactor.** Improve the code without changing the tests.
- After each cycle: invariants live in code (`check_invariants(s) -> bool`); property test uses oracle pattern; ops are generated, not enumerated.

**Artifacts.** Test files first; implementation after. Coverage isn't the metric — *property coverage of invariants* is. A custom structure with one example test and no property test has a coverage *gap*, not a coverage triumph.

**How it lands on dsa-pro.** dsa-pro is designed for this — `references/verification.md` is literally the playbook, `scripts/proptest.{ts,py,rs}` is the scaffold. Every non-trivial pick from `decision-tree.md` gets paired with the *invariant from `catalogue.md`* compiled to a runtime check. The "trap" column of the decision tree is a property-test prompt list.

**Anti-patterns.**

- **Test-after labeled as TDD.** Common, and corrosive — it locks in whatever the implementation happens to do.
- **One property test for ten structures.** Each structure has its own invariants; they don't share.
- **Property tests with example-shaped generators.** If your generator only produces "valid" inputs, you're not fuzzing; expand the strategy.

---

## Waterfall / phased (regulated)

**Pitch.** Requirements → design → implementation → verification → validation → release, with formal handoff and traceability at each gate. Cost of late discovery is high; cost of process is paid up front.

**When to reach for it.** Regulated software (FDA 21 CFR 820 / IEC 62304 for medical, DO-178C for avionics, ISO 26262 for automotive, IEC 61508 for industrial, SOX for finance back-office). Hardware-software co-design with long fab cycles. Government contracts. Any context where "we discovered a bug in prod" is potentially criminal.

**When not to.** Anything where the requirement is exploratory, or where you can iterate cheaply. Most consumer software.

**Cadence and ceremony.**

- **URS** (User Requirements Spec) → **SRS** (Software Requirements Spec) → **SDS** (Software Design Spec) → **Implementation** → **V&V** (Verification & Validation) → **Release**.
- **Traceability matrix** — every requirement maps to a design element, to an implementation artifact, to a verification test, to a validation outcome. This is the deliverable, not a side effect.
- **Formal reviews at each gate.** Sign-off from named roles (engineering, QA, regulatory).
- **Change control.** A change at one stage triggers re-verification at all downstream stages.

**Artifacts.** URS, SRS, SDS, traceability matrix, V&V protocols + reports, risk management file (ISO 14971 for medical), DHF (Design History File for FDA Class II/III). See [`templates.md`](templates.md) → *Traceability matrix*, *Risk management file*.

**How it lands on dsa-pro.** Each non-trivial structure / algorithm pick from `catalogue.md` / `algorithms.md` becomes a row in the SDS, with the *invariant* from `catalogue.md` as the requirement, the property test from `verification.md` as the verification artifact, and the bench numbers as part of validation. The "trap" column maps to risk file entries. Persistence picks (B-tree vs LSM) need explicit crash-safety verification protocols.

**Anti-patterns.**

- **Cosplay waterfall.** Filing the artifacts without doing the analysis. Auditors notice.
- **Process-as-deliverable.** The process should keep the software safe; if the process is the only thing being produced, you're shipping bureaucracy.
- **Skipping V-model.** Verification (does it meet the spec?) and Validation (does the spec meet user needs?) are different and both required.
- **Re-verification avoidance** via stealth changes. Always — *always* — file the ECR.

---

## DDD / hexagonal / clean architecture

**Pitch.** *Not* an SDLC by itself — an architectural style that pairs with any SDLC above. Push business complexity into a typed, isolated **domain core**; isolate I/O, persistence, and UI behind **ports** and **adapters**. The domain doesn't know what database it's in.

**When to reach for it.** Complex domain (insurance, banking, healthcare claims, logistics) where the rules are the product. Multi-team codebases where bounded contexts let teams move independently. Any system where you'd otherwise put SQL into your controllers.

**When not to.** CRUD-shaped tools where the "domain logic" is `if not empty then save`. The ceremony of ports / adapters is overhead.

**Core ideas.**

- **Bounded contexts.** A model is only consistent inside its context. The Order model in *sales* is not the same Order in *fulfillment*. Translate at the seam.
- **Ubiquitous language.** Domain words mean exactly one thing inside one context. If devs and PMs use different words for the same thing, you have a vocabulary bug.
- **Entities (identity-bearing) vs. value objects (equality by content).**
- **Aggregates.** A consistency boundary owned by a single transaction. Avoid cross-aggregate transactions.
- **Domain events.** Things that *happened* in the domain (past tense). Trigger downstream side effects via event handlers.
- **Hexagonal / ports & adapters.** Domain depends on nothing; adapters depend on domain.

**Artifacts.** Context map, domain model diagrams, event storming output, ADRs for context boundaries. See [`templates.md`](templates.md) → *Context map*, *ADR*.

**How it lands on dsa-pro.**

- The **bounded context** is the natural unit at which to run dsa-pro's implementation workflow. Each context has its own operations + access patterns + N.
- A **port** is a small interface. The decision-tree pick for the structure behind the port lives in the *adapter*, not in the domain. The adapter can change (in-memory → Redis → Postgres) without touching the core.
- **Aggregates as invariant boundaries.** The invariant from `verification.md` is enforced inside the aggregate's transactional boundary. Property tests at the aggregate level catch consistency bugs.
- **Read models vs write models (CQRS).** The write model uses one structure (e.g., B-tree-backed table for OLTP), the read model another (e.g., projection into a HashMap or a search index). dsa-pro is exactly the right tool to pick each.

**Anti-patterns.**

- **Anemic domain model.** Entities are just data-bags; logic leaks into service layers. The whole point was to put logic in the model.
- **"Domain Driven Design" with no domain expert in the room.** Then you're just naming services in business words.
- **Hexagonal cosplay.** Five layers of indirection around `SELECT * FROM users`. The architecture earns its keep against complexity; if there's none, it's drag.

---

## Combining traditions

Common, productive combinations:

- **Lean + trunk-based + ADRs.** Early-stage. Move fast; record decisions; iterate. Upgrade later.
- **Scrum + DevOps + TDD-for-cores.** The default for mature SaaS. Sprints set cadence; CI/CD delivers; TDD locks down algorithm-heavy modules.
- **DDD + Scrum + DevOps + TDD.** Complex domains, mature teams. Bounded contexts contain team boundaries; sprints set rhythm; CI/CD delivers; TDD protects the domain core. The most common "senior-shop default."
- **Waterfall + DevOps tooling + DDD seams.** Regulated. The process is phased and audited; the tooling is modern (CI, observability, infrastructure-as-code); the architecture isolates the regulated core from the rapidly-evolving UI.

Anti-combinations:

- **Scrum + Waterfall handoffs ("mini-waterfall sprints").** All ceremony, no agility.
- **Lean + DDD.** Almost always premature. You don't know the domain yet — modeling it in detail is theater.
- **Pure Waterfall + trunk-based.** Audit needs the gate; trunk-based bypasses it. Pick a hybrid intentionally, with the auditor in the room.

---

## How SDLC choice changes dsa-pro's workflow

| SDLC | Where DSA picks live | When verification runs | What artifact captures the decision |
| --- | --- | --- | --- |
| Lean | In code, kept simple | Manually until measurement justifies | None until it matters — then an ADR |
| Agile (Scrum) | In story design notes | Per story, in CI on PR | Sprint backlog story + DoD checklist |
| Kanban | In ticket | Per ticket, in CI on PR | Ticket + ADR for non-obvious picks |
| DevOps / trunk-based | In small PRs | Every push, in CI | PR description + ADR |
| TDD | In test first, then implementation | Continuously while developing | Test file + ADR |
| Waterfall | In SDS, traced from SRS | At V&V gate, also in CI | SDS + traceability matrix row |
| DDD | In adapter (not domain) | Per bounded context, in CI | Context map + ADR |

The picks themselves (`decision-tree.md` → reach for X, fall back Y, trap Z) don't change. What changes is the *paperwork around them* and the *cadence at which they're verified*.

A senior eng working in *all* of these traditions over a career should be able to:

1. Hold an opinion about which SDLC fits the project from one paragraph of description.
2. Defend that opinion against the user's preference if the user's preference would cost them their company / certification / job.
3. Re-derive the same DSA pick under any SDLC — only the wrapper changes.

This skill is built to do all three.
