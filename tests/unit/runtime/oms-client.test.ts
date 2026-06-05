import { describe, expect, it } from 'vitest'
import { createOmsClient } from '../../../src/runtime/http/oms-client'

describe('createOmsClient', () => {
  it('adds bearer auth when performing GET requests', async () => {
    let captured: { url: string; init?: RequestInit } | undefined

    const client = createOmsClient(
      {
        baseUrl: 'https://omsv2-staging.item.com',
        tenantId: 'LT',
        merchantNo: 'LAN0000002'
      },
      async () => 'token-123',
      async (url, init) => {
        captured = { url, init }
        return {
          ok: true,
          json: async () => ({ ok: true })
        } as Response
      }
    )

    await client.get('/api/iam/user-info')

    expect(captured).toEqual({
      url: 'https://omsv2-staging.item.com/api/iam/user-info',
      init: {
        method: 'GET',
        headers: {
          Authorization: 'Bearer token-123',
          'x-tenant-id': 'LT'
        }
      }
    })
  })
})
