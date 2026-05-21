/**
 * Property-test scaffold (TypeScript / fast-check) using the oracle pattern.
 *
 * The oracle pattern is the single highest-value test for a custom data
 * structure (see references/verification.md). Generate a random sequence of
 * operations, apply it to both your custom structure and a trivially correct
 * reference (the "oracle"), and assert that observable behavior matches after
 * every op.
 *
 * To adapt:
 *   1. Replace `MyStructure` and `Oracle` with your real classes.
 *   2. Edit the `Op` discriminated union + the arbitrary to match your API.
 *   3. Implement `applyOp` for both sides.
 *   4. Implement `observableState` so the assert compares everything the caller can see.
 *   5. Implement `checkInvariants` to encode the structure's defining property.
 *
 * Run:
 *   npm install --save-dev fast-check vitest @types/node
 *   npx vitest run scripts/proptest.ts
 *
 * (Vitest is used here; the test bodies translate cleanly to Jest by swapping
 * the imports.)
 */

import { describe, test, expect } from "vitest";
import fc from "fast-check";

// ---------------------------------------------------------------------------
// 1. Replace these with your real types.
// ---------------------------------------------------------------------------

class MyStructure {
  private items = new Map<number, string>();

  insert(k: number, v: string): void {
    this.items.set(k, v);
  }

  delete(k: number): void {
    this.items.delete(k);
  }

  lookup(k: number): string | undefined {
    return this.items.get(k);
  }

  iterSorted(): [number, string][] {
    return Array.from(this.items.entries()).sort(([a], [b]) => a - b);
  }

  checkInvariants(): boolean {
    // Encode the structure's defining property here.
    for (const [k, v] of this.items.entries()) {
      if (typeof k !== "number" || typeof v !== "string") return false;
    }
    return true;
  }
}

class Oracle {
  private items = new Map<number, string>();

  insert(k: number, v: string): void {
    this.items.set(k, v);
  }

  delete(k: number): void {
    this.items.delete(k);
  }

  lookup(k: number): string | undefined {
    return this.items.get(k);
  }

  iterSorted(): [number, string][] {
    return Array.from(this.items.entries()).sort(([a], [b]) => a - b);
  }
}

// ---------------------------------------------------------------------------
// 2. Op model. Edit to match your API.
// ---------------------------------------------------------------------------

type Op =
  | { kind: "insert"; k: number; v: string }
  | { kind: "delete"; k: number }
  | { kind: "lookup"; k: number }
  | { kind: "iter" };

const opArb: fc.Arbitrary<Op> = fc.oneof(
  fc.record({
    kind: fc.constant("insert" as const),
    k: fc.integer({ min: -100, max: 100 }),
    v: fc.string({ maxLength: 8 }),
  }),
  fc.record({
    kind: fc.constant("delete" as const),
    k: fc.integer({ min: -100, max: 100 }),
  }),
  fc.record({
    kind: fc.constant("lookup" as const),
    k: fc.integer({ min: -100, max: 100 }),
  }),
  fc.record({
    kind: fc.constant("iter" as const),
  }),
);

// ---------------------------------------------------------------------------
// 3. Apply + observe.
// ---------------------------------------------------------------------------

function applyOp(s: MyStructure | Oracle, op: Op): unknown {
  switch (op.kind) {
    case "insert":
      s.insert(op.k, op.v);
      return undefined;
    case "delete":
      s.delete(op.k);
      return undefined;
    case "lookup":
      return s.lookup(op.k);
    case "iter":
      return s.iterSorted();
  }
}

function observableState(s: MyStructure | Oracle): [number, string][] {
  return s.iterSorted();
}

// ---------------------------------------------------------------------------
// 4. The actual property tests.
// ---------------------------------------------------------------------------

describe("MyStructure (proptest scaffold)", () => {
  test("oracle pattern: observable behavior matches a reference impl", () => {
    fc.assert(
      fc.property(fc.array(opArb, { maxLength: 200 }), (ops) => {
        const custom = new MyStructure();
        const oracle = new Oracle();
        for (const op of ops) {
          const rCustom = applyOp(custom, op);
          const rOracle = applyOp(oracle, op);
          expect(rCustom).toEqual(rOracle);
          expect(custom.checkInvariants()).toBe(true);
        }
        expect(observableState(custom)).toEqual(observableState(oracle));
      }),
      { numRuns: 200 },
    );
  });

  test("invariants hold after every op", () => {
    fc.assert(
      fc.property(fc.array(opArb, { maxLength: 200 }), (ops) => {
        const s = new MyStructure();
        for (const op of ops) {
          applyOp(s, op);
          expect(s.checkInvariants()).toBe(true);
        }
      }),
      { numRuns: 200 },
    );
  });

  test("insert/delete roundtrip", () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.tuple(fc.integer({ min: -100, max: 100 }), fc.string({ maxLength: 8 })),
          { maxLength: 200 },
        ),
        (items) => {
          const s = new MyStructure();
          const dedup = new Map<number, string>();
          for (const [k, v] of items) {
            s.insert(k, v);
            dedup.set(k, v);
          }
          for (const [k, v] of dedup) {
            expect(s.lookup(k)).toBe(v);
          }
          for (const k of dedup.keys()) {
            s.delete(k);
          }
          for (const k of dedup.keys()) {
            expect(s.lookup(k)).toBeUndefined();
          }
        },
      ),
      { numRuns: 100 },
    );
  });
});

// ---------------------------------------------------------------------------
// 5. Stateful (fc.commands) version — sometimes finds bugs the flat
//    `fc.property` style misses. Use when ops interact strongly with state.
// ---------------------------------------------------------------------------

type Model = { keys: Map<number, string> };

class InsertCommand implements fc.Command<Model, MyStructure> {
  constructor(readonly k: number, readonly v: string) {}
  check(_m: Readonly<Model>): boolean {
    return true;
  }
  run(m: Model, s: MyStructure): void {
    s.insert(this.k, this.v);
    m.keys.set(this.k, this.v);
    expect(s.checkInvariants()).toBe(true);
  }
  toString(): string {
    return `insert(${this.k}, ${JSON.stringify(this.v)})`;
  }
}

class DeleteCommand implements fc.Command<Model, MyStructure> {
  constructor(readonly k: number) {}
  check(_m: Readonly<Model>): boolean {
    return true;
  }
  run(m: Model, s: MyStructure): void {
    s.delete(this.k);
    m.keys.delete(this.k);
    expect(s.checkInvariants()).toBe(true);
  }
  toString(): string {
    return `delete(${this.k})`;
  }
}

class LookupCommand implements fc.Command<Model, MyStructure> {
  constructor(readonly k: number) {}
  check(_m: Readonly<Model>): boolean {
    return true;
  }
  run(m: Model, s: MyStructure): void {
    expect(s.lookup(this.k)).toEqual(m.keys.get(this.k));
  }
  toString(): string {
    return `lookup(${this.k})`;
  }
}

const commandArb = fc.commands(
  [
    fc
      .tuple(fc.integer({ min: -100, max: 100 }), fc.string({ maxLength: 8 }))
      .map(([k, v]) => new InsertCommand(k, v)),
    fc.integer({ min: -100, max: 100 }).map((k) => new DeleteCommand(k)),
    fc.integer({ min: -100, max: 100 }).map((k) => new LookupCommand(k)),
  ],
  { maxCommands: 200 },
);

describe("MyStructure (stateful)", () => {
  test("stateful command sequences preserve invariants", () => {
    fc.assert(
      fc.property(commandArb, (cmds) => {
        const setup = () => ({ model: { keys: new Map<number, string>() }, real: new MyStructure() });
        fc.modelRun(setup, cmds);
      }),
      { numRuns: 200 },
    );
  });
});
