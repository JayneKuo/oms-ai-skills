import { describe, expect, it } from 'vitest'
import { runAgentByName } from '../../../src/cli/index'

describe('runAgentByName', () => {
  it('executes the selected agent from the registry', async () => {
    const result = await runAgentByName(
      {
        get: () => ({ name: 'auth', execute: async () => ({ ok: true, agent: 'auth' }) })
      },
      'auth',
      undefined
    )

    expect(result).toEqual({ ok: true, agent: 'auth' })
  })
})
