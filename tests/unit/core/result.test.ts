import { describe, expect, it } from 'vitest'
import { failResult, okResult } from '../../../src/core/result'

describe('result helpers', () => {
  it('creates ok and failure result envelopes', () => {
    expect(okResult({ value: 1 })).toEqual({ ok: true, data: { value: 1 } })
    expect(failResult('boom')).toEqual({ ok: false, error: 'boom' })
  })
})
