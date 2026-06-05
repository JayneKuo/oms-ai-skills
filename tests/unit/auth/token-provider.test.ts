import { describe, expect, it } from 'vitest'
import { createOmsContext } from '../../../src/config/oms-context'
import { createTokenProvider } from '../../../src/runtime/auth/token-provider'

describe('createTokenProvider', () => {
  it('builds a password grant token request from OMS context', async () => {
    const context = createOmsContext({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'staging-client-id',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'test-user@example.com',
      password: 'test-password'
    })

    let captured: { url: string; init?: RequestInit } | undefined
    const provider = createTokenProvider(context, async (url, init) => {
      captured = { url, init }
      return {
        ok: true,
        json: async () => ({ data: { access_token: 'token-123' } })
      } as Response
    })

    const token = await provider.getAccessToken()

    expect(token).toBe('token-123')
    expect(captured).toEqual({
      url: 'https://omsv2-staging.item.com/api/linker-oms/opc/iam/token',
      init: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-tenant-id': 'LT'
        },
        body: JSON.stringify({
          grantType: 'password',
          username: 'test-user@example.com',
          password: 'test-password'
        })
      }
    })
  })
})
