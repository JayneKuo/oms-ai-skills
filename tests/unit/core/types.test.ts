import { describe, expect, it } from 'vitest'
import { createAgentResult } from '../../../src/core/types'

describe('createAgentResult', () => {
  it('creates a normalized agent result shape', () => {
    expect(
      createAgentResult('auth', true, { hasToken: true }, { username: 'test-user@example.com' })
    ).toEqual({
      agent: 'auth',
      ok: true,
      summary: { hasToken: true },
      data: { username: 'test-user@example.com' }
    })
  })
})
