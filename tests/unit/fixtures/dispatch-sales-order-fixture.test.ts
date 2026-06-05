import { describe, expect, it } from 'vitest'
import fixture from '../../fixtures/dispatch/sales-order.json'

describe('dispatch sales-order fixture', () => {
  it('contains at least one order item for live dispatch smoke', () => {
    expect(Array.isArray(fixture.items)).toBe(true)
    expect(fixture.items.length).toBeGreaterThan(0)
  })
})
