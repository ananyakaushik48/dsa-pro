# Templates

Drop-in templates for the artifacts referenced across [`SKILL.md`](../SKILL.md), [`sdlc.md`](sdlc.md), and [`project-planning.md`](project-planning.md). Each is meant to be *short enough to actually fill in* and re-read. If a template is longer than the work it describes, it's the wrong template.

Run `scripts/scaffold_project.py` to write these as starter files into a `project/` directory, then fill them in conversationally.

## Contents

1. [Discovery brief](#discovery-brief)
2. [PRD (Product Requirements Doc)](#prd-product-requirements-doc)
3. [ADR (Architecture Decision Record)](#adr-architecture-decision-record)
4. [Work breakdown structure (WBS)](#work-breakdown-structure-wbs)
5. [Story](#story)
6. [Sprint plan](#sprint-plan)
7. [Definition of Done](#definition-of-done)
8. [Risk register](#risk-register)
9. [Postmortem](#postmortem)
10. [Traceability matrix (regulated)](#traceability-matrix-regulated)
11. [Risk management file (ISO 14971-style)](#risk-management-file-iso-14971-style)
12. [Context map (DDD)](#context-map-ddd)
13. [Verification plan](#verification-plan)
14. [Module spec](#module-spec)

---

## Discovery brief

A one-pager that ends discovery. Anyone reading it should be able to defend the project's reason for existing.

```markdown
# Discovery Brief: <project name>

**Date.** YYYY-MM-DD
**Owner.** <name>
**Status.** Discovery | Planning | In flight | Shipped | Killed

## Problem
One paragraph. What problem, for whom, and what happens today when they hit it.

## Users
Who they are, how many, how often they hit the problem, what they do instead today.

## Success measure
The single number that says we won. Include the time horizon ("by Q4 2026, X%").

## Constraints
- Compliance / regulatory: <none | HIPAA | PCI | FDA Class II | ...>
- Latency / scale: <P99 < 100ms at 1k QPS | offline OK | ...>
- Budget / runway: <$X / N months / N engineers>
- Team: <who, what languages and stacks>
- Hard deadline: <date or none>
- Soft deadline: <date or none>

## Adjacent systems
What this connects to (DBs, queues, identity, billing, other services) and where the seams are.

## What can we ship if we cut everything cuttable?
The honest MVP.

## Unknowns
- <unknown 1, with plan to resolve (spike, prototype, customer interview, ...) >
- <unknown 2 ...>

## Decision
Build / don't build / spike further. If build → SDLC choice (will be revisited in an ADR).
```

---

## PRD (Product Requirements Doc)

A PRD answers *what we're building and why*. It is not a design doc — implementation goes elsewhere.

```markdown
# PRD: <feature / product name>

**Status.** Draft | Reviewed | Approved | Shipped
**Owner.** <name>  **Engineering lead.** <name>  **Designer.** <name | n/a>

## Problem and users
(2–4 sentences. The user, the problem, the impact.)

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
Numbered for later traceability:

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
What this PRD explicitly does not cover (saves the "but it doesn't do X" review cycle).

## Open questions
- <Q1>
- <Q2>

## Appendix: alternatives considered (briefly)
- <Alt 1>: <why not>
- <Alt 2>: <why not>
```

---

## ADR (Architecture Decision Record)

Recording *why* a decision was made matters more than recording the decision. ADRs are append-only and versioned in the repo. Use the **lightweight** version for most calls; the **full** version for the few decisions that, if reversed, would cost a week+ of work.

### Lightweight ADR

```markdown
# ADR-NNNN: <title in present tense, e.g., "Use Postgres for primary OLTP store">

**Date.** YYYY-MM-DD  **Status.** Proposed | Accepted | Superseded by ADR-NNNN

## Context
2–4 sentences. What forces are at play.

## Decision
What we chose, in one sentence.

## Consequences
- Positive: <...>
- Negative: <...>
- Neutral: <...>
```

### Full ADR

```markdown
# ADR-NNNN: <title>

**Date.** YYYY-MM-DD  **Status.** Proposed | Accepted | Deprecated | Superseded by ADR-NNNN
**Deciders.** <names>

## Context and problem statement
Background. What forces are at play. Constraints from the PRD or discovery brief.

## Decision drivers
- <Driver 1 (e.g., team familiarity)>
- <Driver 2 (e.g., latency budget)>
- ...

## Considered options
1. <Option A>
2. <Option B>
3. <Option C>

## Decision
We chose <option>. <Reason in one paragraph.>

## Pros and cons of each option

### Option A
- Pros: <...>
- Cons: <...>

### Option B
- Pros: <...>
- Cons: <...>

### Option C
- Pros: <...>
- Cons: <...>

## Consequences
- Positive: <...>
- Negative: <...>
- What this constrains downstream: <...>

## Links
- Related ADRs: <...>
- PRDs / RFCs: <...>
- Spike write-ups: <...>
```

---

## Work breakdown structure (WBS)

A WBS turns modules into milestones into tickets. Keep it readable in one screen if possible.

```markdown
# WBS: <project>

## Milestone 1 — <demo-able outcome> (target: <week N>)
**Risks retired this milestone.** <list>
**Modules touched.** <list of module names>

- [ ] WBS-1.1 — <ticket title> — owner: <name> — size: S/M/L/XL
- [ ] WBS-1.2 — <ticket title> — owner: <name> — size: S/M/L/XL
- [ ] WBS-1.3 — <ticket title> — owner: <name> — size: S/M/L/XL

## Milestone 2 — <demo-able outcome> (target: <week M>)
...

## Cross-cutting work
- [ ] WBS-CC.1 — observability dashboards
- [ ] WBS-CC.2 — load test harness
- [ ] WBS-CC.3 — runbook
```

T-shirt sizes: S = a typical PR. M = ~3 PRs of work. L = a sprint. XL = "I don't know, needs a spike." Anything XL gets decomposed before it's allowed to stay in the plan.

---

## Story

A unit of work small enough to merge as one PR, ideally.

```markdown
**ID.** STORY-NNN  **Owner.** <name>  **Size.** S/M/L
**Sprint.** <if Scrum>  **Status.** Ready / In progress / Review / Done

## User-facing description
As a <user>, I want <ability> so that <outcome>.

## Technical notes
- <implementation detail or constraint>
- <decision link, e.g., ADR-0012>
- <data-structure choice, if non-trivial: structure + fallback + trap>

## Dependencies
- Blocks: <STORY-XXX>
- Blocked by: <STORY-YYY>

## Acceptance criteria
- [ ] <observable behavior 1>
- [ ] <observable behavior 2>
- [ ] Tests: <unit / property / integration; which invariants are covered>
- [ ] Docs updated: <where>
- [ ] Telemetry: <metrics added>
- [ ] If non-trivial DSA: invariant function + property test (oracle pattern) shipped
```

---

## Sprint plan

For Scrum-style work. One per sprint.

```markdown
# Sprint <N> — <date range>

## Sprint goal
One sentence. The single outcome this sprint exists to produce.

## Committed stories
- [ ] STORY-001 — <title> — <owner> — <size>
- [ ] STORY-002 — <title> — <owner> — <size>
- [ ] STORY-003 — <title> — <owner> — <size>

## Pulled forward (stretch)
- [ ] STORY-004 — <title>

## Sprint risks
- <Risk 1 and mitigation>
- <Risk 2 and mitigation>

## Definition of Done for this sprint
<the team's standing DoD, or any sprint-specific addenda>
```

---

## Definition of Done

A single short list per project (or per team) that anyone can point at when asked "is this done?"

```markdown
# Definition of Done

A story is "Done" when:

- [ ] Code merged to trunk
- [ ] All tests (unit + property + integration) pass in CI
- [ ] If touching a non-trivial DSA: invariant function + property test (oracle pattern) + microbench in CI
- [ ] PR reviewed and approved by at least one other engineer
- [ ] Docs updated (README / runbook / API doc as applicable)
- [ ] Observability hooked up: metrics + logs at the right verbosity
- [ ] Deployed to staging and exercised
- [ ] Feature flag rolled out (if applicable) or removed
- [ ] No new TODO without a tracked ticket
```

Variants for SDLC contexts in [`sdlc.md`](sdlc.md).

---

## Risk register

A live document. Each row is reviewed periodically; trigger conditions get *measured*.

```markdown
# Risk Register

| ID | Risk | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation | Owner | Trigger to act | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | <description> | M | H | <mitigation> | <owner> | <measurable trigger> | Open / Mitigated / Retired |
| R-002 | LSM compaction stalls under burst | M | H | Tune compaction concurrency; add write-stall metric; load test the burst | <owner> | P95 write latency > 100 ms in load test | Open |
```

Periodicity: weekly in Lean / Agile; per gate in Waterfall. Most projects have 5–15 rows. If your register has 80 rows, you're not tracking risks — you're papering.

---

## Postmortem

For incidents, but also useful after a missed milestone or a notably costly bug. **Blameless.**

```markdown
# Postmortem: <incident or event>

**Date.** YYYY-MM-DD  **Severity.** SEV-1 / SEV-2 / SEV-3
**Authors.** <names>  **Reviewed.** <by whom>

## Summary
One paragraph. What happened, who was affected, how long, how it ended.

## Impact
- Users affected: <number / segment>
- Duration: <start → mitigated → fully resolved>
- Revenue / SLA: <if applicable>

## Timeline (UTC)
- HH:MM — <event>
- HH:MM — <event>
- HH:MM — mitigation deployed
- HH:MM — fully resolved

## Root cause
The actual mechanism, not the proximate trigger. Often a "5 whys" chain.

## What went well
- <thing 1>
- <thing 2>

## What went poorly
- <thing 1>
- <thing 2>

## Where we got lucky
- <thing 1>

## Action items
| ID | Action | Owner | Due | Status |
| --- | --- | --- | --- | --- |
| AI-1 | <add metric, fix bug, update runbook> | <owner> | <date> | Open / Done |
```

Action items without owners and due dates are wishes.

---

## Traceability matrix (regulated)

For phased / regulated work. Every requirement traces to design, implementation, and verification.

```markdown
# Traceability Matrix

| Req ID | Requirement | Design ref | Code ref | Verification ref | V&V outcome | Status |
| --- | --- | --- | --- | --- | --- | --- |
| FR-001 | <statement> | SDS §3.2 | src/order/state.py | test/test_order_state_props.py | PASS 2026-05-12 | Closed |
| FR-002 | <statement> | SDS §3.3 | src/order/ship.py | test/test_shipping.py + V&V protocol VV-7 | PASS 2026-05-15 | Closed |
| NFR-001 | <statement> | SDS §4.1 | infra/loadgen/ | V&V protocol VV-12 | PASS | Closed |
```

The point isn't the document, it's the *coverage* — every requirement must have all five non-status cells filled before release.

---

## Risk management file (ISO 14971-style)

For medical-device or similarly regulated work. Each hazard is identified, evaluated, and mitigated; the residual risk is documented.

```markdown
# Risk Management File

## Hazard inventory

| ID | Hazard | Hazardous situation | Harm | Severity (1–5) | Probability (1–5) | Risk score | Mitigation | Residual risk | Verified by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-001 | <description> | <when it occurs> | <patient harm> | 4 | 2 | 8 | <controls> | 4 | <test ref> |
```

Mitigations themselves can introduce new hazards (control of control); rerun the analysis for the post-mitigation state.

---

## Context map (DDD)

For DDD work. Names bounded contexts and the relationship at each seam.

```markdown
# Context Map

## Contexts
- **Sales.** Quotes, orders, pricing. Owns the *Customer-as-Buyer* model.
- **Fulfillment.** Picking, packing, shipping. Owns the *Order-as-Shipment* model.
- **Billing.** Invoicing, payments, refunds. Owns the *Order-as-Receivable* model.
- **Identity.** Authentication, authorization, accounts. Pure infrastructure context.

## Relationships
| Upstream | Downstream | Relationship | Translation |
| --- | --- | --- | --- |
| Sales | Fulfillment | Customer/Supplier | Order events translated; Sales Order → Fulfillment Shipment |
| Sales | Billing | Customer/Supplier | Order events translated; Sales Order → Billing Receivable |
| Identity | All | Shared Kernel | Account ID is shared identifier across contexts |
| Sales | Legacy CRM | Anti-Corruption Layer | CRM model translated at boundary; CRM concepts don't leak in |

## Ubiquitous language disambiguation
- "Order" means: Sales = *thing the customer agreed to buy*. Fulfillment = *thing to ship*. Billing = *thing to invoice*. Same word, three models. Translation happens at every seam.
- "Customer" means: Sales = *buyer*. Identity = *account holder*. (Not always the same person.)
```

---

## Verification plan

For a module or feature. Lists the tests, what they cover, and how to run them.

```markdown
# Verification Plan: <module or feature>

## Invariants
- <Invariant 1> — encoded in `check_invariants_X()` at `src/path/to/module.py:Lnnn`
- <Invariant 2> — type-system enforced (see `parse, don't validate`)

## Test layers

| Layer | Framework | Coverage of invariants | Where |
| --- | --- | --- | --- |
| Unit | <pytest / cargo test / ...> | Examples per branch | `tests/unit/` |
| Property | <hypothesis / fast-check / proptest> | Oracle pattern (random op sequences vs reference) | `tests/property/` |
| Integration | <pytest / playwright / ...> | Cross-module behavior | `tests/integration/` |
| Fuzz | <atheris / libFuzzer / ...> | Random byte inputs, coverage-guided | `fuzz/` |
| Bench | <criterion / pytest-benchmark / tinybench> | Performance regressions per access pattern | `bench/` |

## Microbench discipline
- Workloads benched: sequential, random, zipfian.
- Warmup: <N iterations>.
- Sample count: <M>.
- Hardware target: <CPU, RAM, allocator, OS>.
- Reporting: median + IQR; regression threshold ±X%.

## CI gating
- Unit + property + integration: blocking.
- Fuzz: nightly, alerts on new crash.
- Bench: nightly, alerts on >X% regression.
```

---

## Module spec

For each module in the architecture decomposition. Five to ten lines is the target.

```markdown
# Module: <name>

**Owner.** <name | "any">  **Layer.** Domain | Application | Adapter | Infrastructure

## Responsibility
One sentence.

## Public interface
- `op_one(arg) -> result` — query / command. Invariant: <...>.
- `op_two(arg) -> result` — query / command. Invariant: <...>.

## Invariants at the seam
- <statement>

## Depends on
- <other module>
- <external system, via which adapter>

## Internal DSA picks (if non-trivial)
- <structure> + fallback <fallback> + trap <trap>. (Per [`decision-tree.md`](decision-tree.md).)

## Verification
See <link to verification plan>.
```
