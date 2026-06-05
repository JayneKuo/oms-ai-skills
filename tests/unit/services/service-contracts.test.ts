import { describe, expect, it } from 'vitest'
import { defineService } from '../../../src/services/service-contract'

describe('defineService', () => {
  it('returns named service metadata and implementation', async () => {
    const service = defineService({
      name: 'iam-service',
      execute: async () => ({ ok: true })
    })

    expect(service.name).toBe('iam-service')
    await expect(service.execute()).resolves.toEqual({ ok: true })
  })
})
