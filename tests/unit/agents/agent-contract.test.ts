import { describe, expect, it } from 'vitest'
import { defineAgent } from '../../../src/agents/base/agent-contract'

describe('defineAgent', () => {
  it('returns agent metadata and execute handler unchanged', async () => {
    const agent = defineAgent({
      name: 'auth',
      description: 'Acquire token and user info',
      execute: async () => ({ ok: true })
    })

    expect(agent.name).toBe('auth')
    expect(agent.description).toBe('Acquire token and user info')
    await expect(agent.execute()).resolves.toEqual({ ok: true })
  })
})
