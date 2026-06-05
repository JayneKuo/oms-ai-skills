import { describe, expect, it } from 'vitest'
import { OmsArchitectureError } from '../../../src/core/errors'

describe('OmsArchitectureError', () => {
  it('captures a message and code', () => {
    const error = new OmsArchitectureError('CONFIG_MISSING', 'Missing config')

    expect(error.code).toBe('CONFIG_MISSING')
    expect(error.message).toBe('Missing config')
  })
})
