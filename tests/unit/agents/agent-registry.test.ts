import { describe, expect, it } from 'vitest'
import { createAgentRegistry } from '../../../src/agents/base/agent-registry'

describe('createAgentRegistry', () => {
  it('stores and resolves agents by name', () => {
    const registry = createAgentRegistry([
      { name: 'auth', execute: async () => ({ ok: true }) },
      { name: 'oms-query', execute: async () => ({ ok: true }) }
    ])

    expect(registry.get('auth')?.name).toBe('auth')
    expect(registry.list()).toEqual(['auth', 'oms-query'])
  })

  it('includes the sales-order agent in registry listings', () => {
    const registry = createAgentRegistry([
      { name: 'auth', execute: async () => ({ ok: true }) },
      { name: 'sales-order', execute: async () => ({ ok: true }) },
      { name: 'oms-query', execute: async () => ({ ok: true }) }
    ])

    expect(registry.get('sales-order')?.name).toBe('sales-order')
    expect(registry.list()).toEqual(['auth', 'sales-order', 'oms-query'])
  })
})
