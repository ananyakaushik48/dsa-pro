# Principles

Engineering principles that the rest of dsa-pro depends on. Each section: **the principle**, **what it actually means in practice**, **how it lands on data-structure and algorithm picks**, **where it can be misapplied**.

These aren't rules; they're priors. A senior engineer holds them in tension — DRY against YAGNI, SOLID against KISS — and resolves the tension *for the case in front of them*. Following one principle past the point where another is screaming is how you build elegant-looking codebases that don't work.

## Contents

1. [Specify before naming](#specify-before-naming)
2. [Boring tech first, stdlib first](#boring-tech-first-stdlib-first)
3. [KISS](#kiss)
4. [YAGNI](#yagni)
5. [DRY (with care)](#dry-with-care)
6. [SOLID](#solid)
7. [Parse, don't validate](#parse-dont-validate)
8. [Make invalid states unrepresentable](#make-invalid-states-unrepresentable)
9. [Principle of least astonishment](#principle-of-least-astonishment)
10. [Quality attributes](#quality-attributes-the-ilities)
11. [Tension and resolution](#tension-and-resolution)

---

## Specify before naming

**Principle.** State what you need (operations + access pattern + N + constraints + invariants) *before* naming a structure, framework, language, or methodology. Most wrong answers happen because the question was wrong.

**In practice.** "I need a tree" is naming. "Read-heavy ordered point + range lookups, ~10 M keys, in-process, single writer, survives crash" is specifying. The second sentence narrows the answer to two or three candidates and rules out a dozen.

**DSA landing.** This is the first step of [`SKILL.md`](../SKILL.md) → *Implementation workflow*, and it's the most important. Every entry in [`decision-tree.md`](decision-tree.md) is keyed on the *want*, not on the structure name. The structures with the loudest brand recognition (red-black tree, Bloom filter, Dijkstra) lose half the time to something more boring.

**Misapplications.** Spec paralysis — asking 30 clarifying questions before suggesting anything. Most projects need 3 questions answered to make a confident pick; ask those, default the rest, and revise when reality disagrees.

---

## Boring tech first, stdlib first

**Principle.** Beating the stdlib, replacing the database, building a custom framework — these are *projects*, not functions. Reach for the boring, battle-tested option until you can *name* what it lacks.

**In practice.** Postgres before specialized DB. `HashMap` before custom hash. Boring language for boring problem. The team you have, the languages they know, the tools they already operate. Novelty has a cost in onboarding, bug discovery, and operational risk; it's worth paying for *only when the boring option's failure mode is what you're trying to escape from*.

**DSA landing.**

- `catalogue.md` repeats this for every family: "C++ `std::unordered_map`, Python `dict`, JS `Map`, Java `HashMap`, Rust `HashMap`, Go `map` already ship battle-tested open-addressing / Robin Hood / etc. Beating them is a project, not a function."
- The "trap" column for custom structures is often: *the stdlib version already solved this; you just didn't know.*
- Custom is justified when you can *name* the lack: "I need cache-line-aligned probing because the workload is 99% L2-miss-bound," not "I want it faster."

**Misapplications.** Boring-tech-fundamentalism. Sometimes the boring option *is* the limit (e.g., Postgres is genuinely wrong for petabyte time-series workloads). Boring-first is a default, not a religion. Conversely: "the team already knows Cassandra" is a real reason to pick Cassandra even when it's somewhat suboptimal.

---

## KISS

**Principle.** *Keep It Simple, Stupid.* Or, less aggressively: simpler than you think it can be.

**In practice.** When you're tempted to add a layer, ask: would the system fail without it? If "no," delete the layer. Each layer (framework, abstraction, indirection) is a *future-you tax* — paid in onboarding, bug-hunting, performance opacity.

**DSA landing.** A 200-line custom B-tree is correct, fast, and maintainable. A 2000-line custom B-tree with a generic key-comparison trait, a pluggable allocator, and three layers of decorators is probably wrong before it ships. Most "general" code is half-used; the unused half is debt. The decision-tree gives you the boring pick; lean on it.

**Misapplications.** "Simple" can mean *fewer-lines* (good) or *naive* (bad). A single 600-line function isn't "simple"; it's tangled. Simple at the right granularity.

---

## YAGNI

**Principle.** *You Aren't Gonna Need It.* Don't build for tomorrow's requirement; you don't know what it is, and tomorrow's you is smarter and has more info.

**In practice.** Features, abstractions, and generality you add "in case" usually expire unused. Worse, they constrain the actual future requirement when it lands. Build the smallest thing that satisfies today's need; if the future need materializes, refactor *then* — you'll have signal you don't have now.

**DSA landing.**

- Adding a parameter to your `HashMap` for *future* concurrency support, when today's code is single-threaded? YAGNI. Pull `DashMap` (or your language's equivalent) when concurrency arrives.
- Designing your own pluggable comparator framework before you have two comparators? YAGNI.
- Making your structure generic over `K, V` when only `String, i64` is actually used? Sometimes YAGNI; sometimes the type system makes it free. Judgment call.

**Misapplications.** Building *trivially*-irreversible decisions YAGNI-style. Choice of database family, of language, of public API shape — these are the decisions where you *do* have to think ahead. YAGNI is for *features*, not *seams*.

---

## DRY (with care)

**Principle.** *Don't Repeat Yourself.* Two pieces of code that say the same thing should usually be one.

**In practice.** The honest version: *the same knowledge* should live in one place. *Coincidentally identical code* often shouldn't be merged — it represents two different concepts that happen to look the same right now.

> "Duplication is far cheaper than the wrong abstraction." — Sandi Metz

**DSA landing.**

- Two structures with the same invariant *check* function? Merge the function. (Same knowledge — the invariant.)
- Two structures that *happen* to have similar method names but different semantics (e.g., two `find` methods, one stable and one not)? Don't merge them; that's coincidence, not shared knowledge.
- Three places that need a Bloom filter sized differently? They share the *Bloom filter*, not the size; parameterize, don't merge into one global filter.

**Misapplications.** Over-DRYing turns simple code into a maze of abstractions. The test: can a new dev read this code and understand it without traversing 4 files? If no, the abstraction is hurting more than the duplication did.

---

## SOLID

Five principles, mainly aimed at OO design but useful anywhere. Each has a one-line spirit.

### Single Responsibility (SRP)

**Principle.** A module has one reason to change.

**Practice.** If two changes that are unrelated in the business sense touch the same file, the file is doing two jobs.

**DSA landing.** A `Cache` class that also handles eviction, persistence, and metrics is four classes pretending to be one. Split. (Then DRY them via composition, not inheritance.)

### Open/Closed (OCP)

**Principle.** Open for extension, closed for modification.

**Practice.** Adding a new variant shouldn't require editing existing code. Use polymorphism, traits, or strategy injection — *when there are actually multiple variants*. Inventing OCP plumbing for a single implementation is YAGNI in OCP clothing.

**DSA landing.** A `PriorityQueue` interface with concrete `BinaryHeap` and `PairingHeap` impls = OCP. A `Tree` interface with one `RedBlackTree` impl and no realistic prospect of others = OCP cosplay.

### Liskov Substitution (LSP)

**Principle.** Subtypes must be usable wherever the parent type is used, *without* surprising the caller.

**Practice.** If `MyDeque` extends `MyQueue` but throws on `enqueue_front`, you've violated LSP. The caller of `MyQueue` doesn't expect that.

**DSA landing.** A `Set` impl that *sometimes* returns duplicates "for performance" violates LSP — the set contract said no duplicates. Either fix it or expose a different interface (`Bag` / `Multiset`). The "trap" column in `decision-tree.md` is often an LSP violation in disguise (e.g., "skip list looks like a sorted map but isn't worst-case O(log n)").

### Interface Segregation (ISP)

**Principle.** Many narrow interfaces beat one wide one.

**Practice.** If a consumer needs `Reader` but you force them to depend on `ReaderWriter`, you've coupled them to mutation they don't use.

**DSA landing.** An *indexed priority queue* exposes more (decrease-key, change-priority) than a plain `PriorityQueue`. Consumers that only push and pop should depend on the smaller interface. This compiles down to: pass the smaller trait / interface / protocol type in function signatures.

### Dependency Inversion (DIP)

**Principle.** Depend on abstractions, not on concretions; especially across architectural seams.

**Practice.** The *domain* doesn't depend on the database; it depends on a `Repository` interface, and the database implementation depends on *the domain's* interface. Hexagonal architecture in [`sdlc.md`](sdlc.md) → *DDD* is exactly this.

**DSA landing.** Your business logic shouldn't import `Postgres` or `Redis` directly. It depends on a small interface like `OrderStore`, which has a Postgres adapter (B-tree-backed in practice) and a memory adapter (HashMap-backed for tests). dsa-pro's picks live in the *adapter*; the domain sees only the interface.

---

## Parse, don't validate

**Principle** (from Alexis King's essay of the same name). Don't *validate* data and then keep using its untyped form — *parse* it into a type that proves the validation already happened, so downstream code can't undo it.

**In practice.**

```
# Validate (anti-pattern)
def process(email: str):
  if not is_email(email): raise ...
  send(email)               # downstream: still type `str`, validation can be lost

# Parse (better)
@dataclass(frozen=True)
class Email:
  value: str
  def __post_init__(self):
    if not is_email(self.value): raise ...

def process(email: Email):
  send(email)               # downstream: type system carries the proof
```

**DSA landing.**

- A `SortedVec<T>` type that can *only* be constructed by sorting is unfooled by callers handing in random arrays. The type *proves* the order invariant.
- A `NonEmpty<T>` type means `head()` / `last()` never need an `Option`. The error is moved to construction time.
- The invariants column in [`catalogue.md`](catalogue.md) often becomes a parser: "the only way to construct this is via the constructor that establishes the invariant." Then `check_invariants` is for *debug* assertions, not runtime correctness — the type carries the proof.

**Misapplications.** Type-system maximalism — encoding so many invariants in the type that the type signatures are unreadable. Balance against readability.

---

## Make invalid states unrepresentable

**Principle.** If a combination of fields is invalid, restructure so that the language can't express that combination.

**In practice.**

```
# Representable invalid state
class Order:
  shipped: bool
  tracking_number: str  # only meaningful if shipped == True

# Unrepresentable
class OrderState:
  enum: Pending | Confirmed | Shipped { tracking_number: str }
```

The second can't accidentally have a tracking number on a Pending order. The compiler enforces it.

**DSA landing.**

- A persistent data structure's "old version" and "new version" should be different *values* of the same type — not nullable pointers, not version flags.
- A lock-free queue's invariants ("the head pointer is never null after init") become unrepresentable-by-construction.
- The "trap" column of [`decision-tree.md`](decision-tree.md) often reduces to "this structure has a representable invalid state that bites you." Either fix the API to make it unrepresentable, or assert in debug + property tests in release.

**Misapplications.** Some invariants genuinely can't be encoded in your language's type system (e.g., "every node in this graph has at least one outgoing edge" — hard to express in most type systems). For these, fall back to runtime checks + property tests.

---

## Principle of least astonishment

**Principle.** APIs should behave the way someone reading the code *expects* them to behave. Surprise = bug.

**In practice.**

- Method names tell the truth: `peek()` doesn't mutate, `pop()` does.
- Comparison operators are total or named otherwise (`==` vs `equiv_under_eps`).
- Side effects are visible from the call site: prefer `read_then_increment(x)` over a mutating `read(x)`.

**DSA landing.**

- A `Vec::insert(i, x)` that's O(n) (because it shifts) is fine if documented; an `insert` on a structure where it sometimes silently rebuilds and sometimes doesn't is a landmine.
- Python's `heapq` is min-only — a max-heap call site has to negate. Surprising the first time; *unsurprising* once you know. dsa-pro flags these in `catalogue.md`.
- Iteration order on hash maps: insertion-ordered in Python and JS, unspecified elsewhere. Code that relies on iteration order on a non-ordered map will surprise on port.

---

## Quality attributes (the -ilities)

When picking a structure, algorithm, framework, or SDLC, the trade-offs live in these axes. Naming them keeps the conversation honest.

### Performance

Throughput (ops/sec) and latency (time per op). Distinguish *peak* from *p50 / p99 / p99.9*. A structure with great average and a 100× tail latency is unfit for real-time / interactive workloads. See [`verification.md`](verification.md) → *Microbench discipline*.

### Scalability

How performance changes as N (or QPS, or concurrency) grows. A great single-node solution that doesn't shard is a future migration. A great distributed solution that's painful at small scale is overbuilt today.

### Reliability

Probability of correct behavior under expected and unexpected conditions. Includes crash safety (does it survive process kill?), durability (does it survive disk loss?), and correctness under load. The verification chapter is mostly about this.

### Availability

Uptime under failure. Drives replication, redundancy, retries, circuit breakers. Often confused with reliability — *reliability* is "it works when called," *availability* is "it's callable."

### Maintainability

How costly is it to change after you ship. Driven by clarity, test coverage, modularity, naming. The DSA pick affects this hard: a custom data structure with no oracle test and no invariant check is a maintenance debt that compounds.

### Security

Confidentiality, integrity, authentication, authorization. Special hot spots in DSA:

- **Hash floods.** Use SipHash / process-keyed seed for user-input keys. ([`catalogue.md`](catalogue.md) → *Hash tables*.)
- **Timing side channels.** Comparison and lookup that branches on secret bits leaks the secret bits. Use constant-time comparison for cryptographic material; consider data-structure choice that doesn't branch on secrets.
- **Memory safety.** Lock-free / intrusive structures in non-GC languages need careful reclamation (hazard pointers, epoch reclamation). Use-after-free is a security bug, not a correctness bug.

### Observability

How visible is the system at runtime. Logs, metrics, traces. A custom structure with no instrumentation is a black box when prod is on fire. At minimum, expose counters: ops/sec, errors/sec, queue depth, cache hit rate.

### Cost

Cloud bill, license fees, dev hours. The "fastest" pick is sometimes 10× more expensive than the "fast enough" one.

### Privacy / compliance

GDPR, HIPAA, PCI, etc. Drives encryption at rest and in transit, retention limits, access auditing, residency. Affects the *data layer* harder than the algorithm layer.

---

## Tension and resolution

These principles disagree all the time. Holding them in tension is the senior engineer's job. Some common tensions:

- **DRY vs. KISS.** Three small duplications are simpler than one clever abstraction. Wait for the fourth duplication before extracting.
- **YAGNI vs. DIP.** YAGNI says don't build the abstraction; DIP says build the interface so you can swap impls. Resolve by *the cost of swapping later*: if cheap, YAGNI wins; if expensive, DIP wins.
- **SRP vs. KISS.** Splitting one 30-line module into three 10-line modules can hurt more than it helps. Split when it *carries cost* to keep together, not on principle.
- **Performance vs. maintainability.** Always solve the maintainability problem first; you can't optimize what you can't read. Then measure; then optimize the hot spot specifically.
- **Type-system-maximalism vs. readability.** Encode the *important* invariants in types; runtime-check the rest. The point is correctness, not type-puzzle solutions.

The shortest summary of this file: **specify before naming, prefer boring, lean on the type system to carry invariants, and resolve tensions in front of the concrete case, not on principle.**
