# Project Planning

The top-down workflow from "I have an idea" to "a team can build this without re-deriving every decision." Walks the conversation through discovery, decomposition, architecture, and sequencing — producing the artifacts as a side effect, not a separate document-writing exercise.

The plan is *a tool the team uses*, not an artifact the team reads once and abandons. Keep it lean enough to be re-read. Anything that can't pass the "would I open this in week 6" test is dead weight.

## Contents

1. [The shape of a useful plan](#the-shape-of-a-useful-plan)
2. [Phase 1: Discovery](#phase-1-discovery)
3. [Phase 2: SDLC choice](#phase-2-sdlc-choice)
4. [Phase 3: Architecture and decomposition](#phase-3-architecture-and-decomposition)
5. [Phase 4: Per-module DSA and verification](#phase-4-per-module-dsa-and-verification)
6. [Phase 5: Sequencing and roadmap](#phase-5-sequencing-and-roadmap)
7. [Phase 6: Risk register and unknowns](#phase-6-risk-register-and-unknowns)
8. [Phase 7: Definition of Done](#phase-7-definition-of-done)
9. [Anti-patterns](#anti-patterns)

---

## The shape of a useful plan

A complete plan, regardless of project size, answers these in order:

1. **What** are we building, **for whom**, with **what success measure**?
2. Under **what constraints** (compliance, latency, budget, team, language, deadline)?
3. **How are we working** (SDLC) and **why that fit**?
4. **What are the parts** (modules / bounded contexts) and the **interfaces between them**?
5. For each non-trivial part, **what's the data structure and algorithm pick**, with fallback and trap, per [`decision-tree.md`](decision-tree.md)?
6. **How will we know it works**? Invariants, property tests, integration tests, benchmarks.
7. **In what order** are we building? Milestones with honest sizes.
8. **What might kill this** and what's the mitigation?
9. **When is something Done**?

The artifacts (PRD, ADRs, WBS, etc.) are the *materialization* of those answers, not the work itself. Many fine projects ship with a one-pager + 4 ADRs + a markdown task list. Many doomed projects ship with a 60-page spec and no working software.

---

## Phase 1: Discovery

**Goal.** Reduce the project from "an idea" to "a problem statement, a success measure, and an explicit list of unknowns."

**Ask only the questions whose answers actually change the plan.** If the answer to "what language" doesn't change whether we ship a backend service or a CLI, don't ask yet.

**Discovery prompts (use the ones that fit).**

- **Problem.** What problem, for whom, and what happens today when they hit it?
- **Users.** Who are they; how many; how often do they encounter the problem; what do they do instead?
- **Success measure.** What's the *one number* that says we won. (If you can't pick one, the goal isn't sharp enough yet.)
- **Constraints.**
  - **Compliance / regulatory.** HIPAA, GDPR, PCI, SOC 2, FDA, etc. Drives SDLC choice hard.
  - **Latency / scale.** Concurrent users, requests/sec, P99 latency targets, data volume.
  - **Budget / runway.** Cash + time. Drives scope ruthlessly.
  - **Team.** Who's on it; what languages and stacks do they know; how many.
  - **Language / platform.** Existing ecosystem, must-integrate-with constraints.
  - **Deadline.** Hard (regulator demo) vs. soft (we'd like Q3).
- **Adjacent systems.** What does this connect to (databases, queues, identity, billing, other services)? Where are the seams?
- **What can we ship if we cut?** If forced to ship in 2 weeks, what's left in? — surfaces the actual MVP.
- **Unknowns.** What don't we know that could move the plan? Name them explicitly.

**Output: Discovery brief.** A one-pager with the answers. Template in [`templates.md`](templates.md) → *Discovery brief*.

**Red flags during discovery.**

- "We need an MLP / blockchain / agent platform" before any user problem is named. *Solution chasing problem.*
- "Just like X but better." Better at *what*, for *whom*?
- "Performance is critical." For which operation, at what scale, with what budget? Push for numbers.
- "Everyone needs this." Then nobody specifically does. Push for a beachhead user.

---

## Phase 2: SDLC choice

**Goal.** Pick the methodology in [`sdlc.md`](sdlc.md) that matches the risk shape of *this project*, not the team's habits.

**Reach for** the decision table at the top of `sdlc.md`. Most projects fall into one of these:

- **Greenfield + uncertain users** → Lean + Kanban + ADRs.
- **Established SaaS + scoped feature** → Scrum + DevOps + TDD for cores.
- **Regulated** → Phased + DDD seams + DevOps tooling for the unregulated edges.
- **Platform / shared library / infra** → Trunk-based + TDD + property tests + microbenches in CI.
- **Brownfield migration** → Strangler-fig + ADRs per swap + extensive monitoring.

**Output: an ADR.** A short Architecture Decision Record naming the SDLC choice, the alternative considered, and the reasons. Template in [`templates.md`](templates.md) → *ADR*.

The SDLC choice can change later — at which point you write *another* ADR superseding the first. Plans evolve; ADRs are append-only.

---

## Phase 3: Architecture and decomposition

**Goal.** Split the system into parts that can be built (and possibly owned) independently. Name the seams; specify the interfaces.

### Where to draw the lines

Three common decomposition strategies, often layered:

1. **By bounded context (DDD).** Best for complex domains with distinct vocabularies. *Sales* and *Fulfillment* have different Order models.
2. **By layer (clean / hexagonal).** Domain core, application services, adapters (DB, HTTP, queues, UI). The dependency graph points *inward* — adapters depend on domain, never the reverse.
3. **By scaling unit.** Hot path vs. cold path; read vs. write; sync vs. async. Drives service splits and CQRS-style splits.

Most real systems use all three at once: hexagonal layers *within* each bounded context, with hot/cold path splits where load demands.

### Specifying a module

For each module, write down — in 5–10 lines, not 5–10 pages:

- **Name.** A noun phrase in the ubiquitous language.
- **Responsibility.** One sentence. If you can't, it's actually two modules.
- **Public interface.** The operations callers depend on (names + types + invariants on input/output). Mark which are *queries* (no side effect) and which are *commands* (state-changing).
- **Invariants.** What must always be true at the seam? (e.g., "An Order is never in 'Shipped' state without a tracking number.")
- **Depends on.** Other modules whose interfaces this module calls.
- **Owned by.** Person / team / "any."
- **Verification strategy.** Unit, property, integration, contract? See [`verification.md`](verification.md).

Stop here. Implementation details (data structure choice, library choice, DB schema) belong in the per-module work; *the seam* is what the rest of the system commits to.

### Architectural decisions worth an ADR

Not every decision needs one. Ones that do:

- Choice of language, runtime, or major framework.
- Choice of database family (RDBMS vs. document vs. KV vs. time-series).
- Choice between sync and async messaging at a seam.
- Choice between monolith and split into services.
- Anything that, if reversed, would cost > 1 week of work.

Each ADR: context, options considered, decision, consequences. Template in [`templates.md`](templates.md).

### Output

- **Context map.** Modules + dependencies. A simple diagram or a markdown table is fine.
- **One short module spec per module.**
- **One ADR per decision worth recording.**

---

## Phase 4: Per-module DSA and verification

**Goal.** For each non-trivial module, run [`SKILL.md`](../SKILL.md) → *Implementation workflow* to pick structures and algorithms.

This is where dsa-pro's original workflow lives. The planning phases above give you, for each module:

- The operations the module exposes.
- The expected access patterns and scale (N, read/write mix, concurrency).
- The constraints (latency, persistence, language).

From there:

1. **Restate as `<operations> + <access pattern> + <N> + <constraints>`.** Per module.
2. **Consult [`decision-tree.md`](decision-tree.md)** for canonical pick + fallback + trap.
3. **Look up structure in [`catalogue.md`](catalogue.md)** for invariants, complexities, language stdlib name, traps.
4. **Find algorithm in [`algorithms.md`](algorithms.md)** if there's traversal / transform / search.
5. **Define verification.** Per `verification.md`: invariant function, oracle pattern test, microbench scaffold from `scripts/`.

### Skip the DSA step when

The module is CRUD-shaped: `dict` or `HashMap` is fine; the DB is `Postgres` because it's everybody else's `Postgres`. Don't manufacture decisions to look busy.

### Output

Per non-trivial module:

- Named structure + algorithm pair + fallback + trap (one line).
- Invariant statement (one line of pseudo-code).
- Verification plan: which property tests, which microbenches, which integration tests.

Across all modules together:

- A *cumulative* verification plan that includes integration boundaries (the seams must hold under cross-module operation).

---

## Phase 5: Sequencing and roadmap

**Goal.** Turn modules into milestones into tickets, in an order that *delivers value early* and *retires the riskiest unknowns first*.

### Two orthogonal orderings

You're ordering by two principles at once:

- **Value delivery.** Ship something a user can use as early as possible. (Drives MVP.)
- **Risk retirement.** Touch the scary modules (novel algorithm, new vendor, regulatory step) early, when there's slack to deal with surprise.

These can conflict. The product manager pulls toward value; the engineering lead pulls toward risk. Both are right; the compromise is usually "ship a vertical slice that touches every risky seam at half-fidelity, then deepen."

### Sizing honestly

T-shirt sizes (S / M / L / XL) beat story points for plan-level estimation. Calibrate by reference: "S = a typical PR by this team this month."

If a milestone has multiple XLs in a row, decompose it. An XL is "I don't really know how long this takes" in coward's clothing.

### Sequencing template

```
Milestone 1 (week 0–N): goal in user terms. Includes modules X, Y, Z. Risks retired: a, b.
Milestone 2 (week N–M): ...
```

Each milestone has:

- A **demo-able outcome** (someone external can see and use it).
- A **set of modules** at a given fidelity (skeleton / MVP / hardened / scaled).
- A **risk retired** for it to make the list.

### Tickets

Inside each milestone, the work is tickets / stories. Each ticket needs:

- **Acceptance criteria.** What does "done" look like for *this* ticket.
- **Dependencies.** What blocks this; what does this unblock.
- **Test plan.** Which tests prove it; if it touches a non-trivial structure, which property tests / benchmarks.

Templates in [`templates.md`](templates.md) → *Work breakdown structure*, *Story*.

---

## Phase 6: Risk register and unknowns

**Goal.** Make the things that scare you visible, with a plan for what to do when they happen.

### A risk register row

| Risk | Likelihood | Impact | Mitigation | Owner | Trigger to act |
| --- | --- | --- | --- | --- | --- |
| LSM compaction stalls writes under burst load | M | H | Tune compaction concurrency; add write-stall metric; load-test the burst | Mr. Save the World | P95 write latency > 100 ms in load test |

Most projects' risk register fits on one page. The point isn't the document — it's that *the conversation about it happened.*

### Risks worth listing

- **Technical.** Novel algorithm, novel vendor, untested scale, untested compliance path, dependency without an obvious fallback.
- **Personnel.** Single point of knowledge, expected attrition, unfilled role.
- **External.** Regulatory ruling pending, vendor pricing change, market shift.
- **Schedule.** Hard deadline with soft requirements; soft deadline with hard requirements is the better failure mode.

### Unknowns

Distinct from risks: things we *don't know yet* (vs. things we know are dangerous). Each unknown has either (a) a spike scheduled to resolve it, or (b) an explicit acknowledgment that we're going to find out the hard way.

---

## Phase 7: Definition of Done

**Goal.** Decide what "shipped" means, before you ship.

Definition of Done isn't a checklist of bureaucracy; it's the assertion you make when you say a thing is finished. It varies by SDLC:

- **Lean MVP.** "Available behind a flag for the pilot cohort; we've measured the success metric for 1 week; we've decided next step."
- **Scrum sprint story.** "Code merged to trunk; tests pass; PR reviewed; docs updated; deployed to staging."
- **Trunk-based / DevOps.** "Merged; CI green; flag rolled to 100% in prod or removed; observability dashboards confirm no regression."
- **TDD / algorithm-heavy.** "Invariants documented; property tests cover op sequences; oracle comparison passes; microbench numbers reported."
- **Waterfall / regulated.** "Implementation complete; SDS updated; traceability matrix populated; V&V protocols executed; risk file updated; sign-off filed."

Template in [`templates.md`](templates.md) → *Definition of Done*.

---

## Anti-patterns

- **Big up-front design.** A 60-page PRD authored in isolation, then handed off. Discovery never happens; the spec rots; the team builds something that solves a different problem.
- **No-plan plan.** "Let's just start." Sometimes works for one solo project; never works for two collaborators.
- **Doc gardening.** Updating the plan more than touching the code. The plan is a *tool*, not the deliverable.
- **Reverse-engineered plan.** Writing the plan to match what was already built. Burns trust; lies to future-you.
- **Risk-register theater.** Filing the risk register and never re-reading it. The trigger conditions in each row should be *measured* periodically.
- **Estimating in absolutes.** "It'll take 6 weeks." Try "S / M / L / XL relative to a typical PR" instead, and report cycle-time empirically as you go.
- **Architecture astronauting.** Adopting hexagonal / CQRS / event-sourcing because they're sophisticated, not because the domain demands them. Drag without payoff.
- **Hero-mode** when the plan slips. The plan slipping is information; learn from it. Pulling all-nighters to "save the plan" trades one bad week for many.

---

The shortest version of this entire file: **discover the problem, pick a process that matches the risk, draw seams, pick structures behind the seams using dsa-pro, sequence by value-and-risk, write down what scares you, agree what done means, and keep all of that lean enough to actually re-read.**
