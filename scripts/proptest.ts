// Property-test scaffold (TypeScript + fast-check).
//
// Install: npm i -D fast-check vitest          (or jest / mocha)
// Run:     npx vitest run proptest.test.ts
//
// Pattern: oracle comparison + invariant check after every op.
// Adapt `MyStructure`, `OracleImpl`, `Op`, and `applyAndCompare`.

import { describe, test, expect } from 'vitest'
import fc from 'fast-check'

// ─── (1) Replace with the candidate ───
class MyStructure<V> {
  private data = new Map<number, V>()
  insert(k: number, v: V): void { this.data.set(k, v) }
  delete(k: number): boolean { return this.data.delete(k) }
  lookup(k: number): V | undefined { return this.data.get(k) }
  size(): number { return this.data.size }

  // Encode the structure's defining invariant(s) here. Return false on violation.
  checkInvariants(): boolean {
    // e.g., for BST: in-order traversal is strictly sorted
    // for heap: every parent ≤ children
    // for hash table: load factor ≤ configured max; all inserted keys retrievable
    return true
  }
}

// ─── (2) Reference: trivially correct, slow is fine ───
class OracleImpl<V> {
  private data: Array<[number, V]> = []
  insert(k: number, v: V): void {
    const i = this.data.findIndex(([kk]) => kk === k)
    if (i >= 0) this.data[i] = [k, v]
    else this.data.push([k, v])
  }
  delete(k: number): boolean {
    const i = this.data.findIndex(([kk]) => kk === k)
    if (i < 0) return false
    this.data.splice(i, 1)
    return true
  }
  lookup(k: number): V | undefined {
    return this.data.find(([kk]) => kk === k)?.[1]
  }
  size(): number { return this.data.length }
}

// ─── (3) Operations the property test will generate ───
type Op =
  | { tag: 'insert'; k: number; v: number }
  | { tag: 'delete'; k: number }
  | { tag: 'lookup'; k: number }

const opArb: fc.Arbitrary<Op> = fc.oneof(
  fc.record({ tag: fc.constant('insert' as const), k: fc.integer(), v: fc.integer() }),
  fc.record({ tag: fc.constant('delete' as const), k: fc.integer() }),
  fc.record({ tag: fc.constant('lookup' as const), k: fc.integer() }),
)

function applyAndCompare(op: Op, c: MyStructure<number>, o: OracleImpl<number>) {
  switch (op.tag) {
    case 'insert':
      c.insert(op.k, op.v); o.insert(op.k, op.v); break
    case 'delete': {
      const a = c.delete(op.k); const b = o.delete(op.k)
      expect(a).toBe(b); break
    }
    case 'lookup': {
      const a = c.lookup(op.k); const b = o.lookup(op.k)
      expect(a).toEqual(b); break
    }
  }
  expect(c.size()).toBe(o.size())
  expect(c.checkInvariants()).toBe(true)
}

// ─── (4) The actual property ───
describe('MyStructure ↔ Oracle', () => {
  test('any sequence of ops preserves observable behavior and invariants', () => {
    fc.assert(
      fc.property(fc.array(opArb, { maxLength: 200 }), (ops) => {
        const c = new MyStructure<number>()
        const o = new OracleImpl<number>()
        for (const op of ops) applyAndCompare(op, c, o)
      }),
      { numRuns: 500, verbose: true },
    )
  })

  test('insert/delete roundtrip leaves structure empty', () => {
    fc.assert(
      fc.property(fc.uniqueArray(fc.integer()), (keys) => {
        const c = new MyStructure<number>()
        for (const k of keys) c.insert(k, k)
        for (const k of keys) c.delete(k)
        expect(c.size()).toBe(0)
        expect(c.checkInvariants()).toBe(true)
      }),
    )
  })
})
