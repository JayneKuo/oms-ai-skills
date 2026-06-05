import { describe, expect, it, vi } from 'vitest'
import { runStagingDispatchLogSmoke } from '../../../src/cli/dispatch-log-smoke-entrypoint'

describe('runStagingDispatchLogSmoke', () => {
  it('queries dispatch logs for a given eventId through the staging bootstrap', async () => {
    const fetchLike = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { access_token: 'token-123' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify([{ eventId: 'evt-123', logs: ['matched warehouse'] }]), {
          headers: { 'Content-Type': 'application/json' }
        })
      )

    await expect(
      runStagingDispatchLogSmoke(
        {
          OMS_BASE_URL: 'https://omsv2-staging.item.com',
          OMS_IAM_BASE_URL: 'https://id-staging.item.com',
          OMS_IAM_CLIENT_ID: 'client-id',
          OMS_TENANT_ID: 'LT',
          OMS_MERCHANT_NO: 'LAN0000002',
          OMS_USERNAME: 'test-user@example.com',
          OMS_PASSWORD: 'test-password'
        },
        'evt-123',
        fetchLike
      )
    ).resolves.toEqual([{ eventId: 'evt-123', logs: ['matched warehouse'] }])

    expect(fetchLike).toHaveBeenNthCalledWith(
      2,
      'https://omsv2-staging.item.com/api/linker-oms/oas/rpc-api/dispatch-log/evt-123',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: 'Bearer token-123' })
      })
    )
  })
})
