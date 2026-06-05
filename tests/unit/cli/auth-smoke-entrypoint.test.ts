import { describe, expect, it, vi } from 'vitest'
import { runStagingAuthSmoke } from '../../../src/cli/auth-smoke-entrypoint'

describe('runStagingAuthSmoke', () => {
  it('reads env-shaped values, builds the staging bootstrap, and returns auth smoke results', async () => {
    const fetchLike = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { accessToken: 'token-123' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { username: 'test-user@example.com' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )

    await expect(
      runStagingAuthSmoke(
        {
          OMS_BASE_URL: 'https://omsv2-staging.item.com',
          OMS_IAM_BASE_URL: 'https://id-staging.item.com',
          OMS_IAM_CLIENT_ID: 'client-id',
          OMS_TENANT_ID: 'LT',
          OMS_MERCHANT_NO: 'LAN0000002',
          OMS_USERNAME: 'test-user@example.com',
          OMS_PASSWORD: 'test-password'
        },
        fetchLike
      )
    ).resolves.toEqual({
      token: { data: { accessToken: 'token-123' } },
      userInfo: { data: { username: 'test-user@example.com' } }
    })
  })
})
