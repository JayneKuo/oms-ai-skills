import { describe, expect, it, vi } from 'vitest'
import { runStagingDispatchSmoke } from '../../../src/cli/dispatch-smoke-entrypoint'

describe('runStagingDispatchSmoke', () => {
  it('submits a sample sales-order dispatch request through the staging bootstrap', async () => {
    const fetchLike = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { access_token: 'token-123' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'SUCCESS', eventId: 'evt-123', dispatchList: [] }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )

    await expect(
      runStagingDispatchSmoke(
        {
          OMS_BASE_URL: 'https://omsv2-staging.item.com',
          OMS_IAM_BASE_URL: 'https://id-staging.item.com',
          OMS_IAM_CLIENT_ID: 'client-id',
          OMS_TENANT_ID: 'LT',
          OMS_MERCHANT_NO: 'LAN0000002',
          OMS_USERNAME: 'test-user@example.com',
          OMS_PASSWORD: 'test-password'
        },
        {
          referenceNo: 'TEST-001',
          orderNo: 'SO-TEST-001',
          items: [],
          defaultRules: [],
          customRules: []
        },
        fetchLike
      )
    ).resolves.toEqual({
      status: 'SUCCESS',
      eventId: 'evt-123',
      dispatchList: []
    })

    expect(fetchLike).toHaveBeenNthCalledWith(
      2,
      'https://omsv2-staging.item.com/api/linker-oms/oas/rpc-api/dispatch/sales-order',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer token-123' }),
        body: JSON.stringify({
          tenantId: 'LT',
          merchantNo: 'LAN0000002',
          referenceNo: 'TEST-001',
          orderNo: 'SO-TEST-001',
          items: [],
          defaultRules: [],
          customRules: []
        })
      })
    )
  })
})
