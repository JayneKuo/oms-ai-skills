import { describe, expect, it, vi } from 'vitest'
import { runStagingShippingMappingSmoke } from '../../../src/cli/shipping-mapping-smoke-entrypoint'

describe('runStagingShippingMappingSmoke', () => {
  it('executes a shipping mapping request through the staging bootstrap', async () => {
    const fetchLike = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { access_token: 'token-123' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ carrierName: 'FedEx', shippingService: 'Ground Home Delivery' }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )

    await expect(
      runStagingShippingMappingSmoke(
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
          channelId: 1,
          inputConditions: {
            carrier: 'FedEx',
            shipMethod: 'Ground'
          }
        },
        fetchLike
      )
    ).resolves.toEqual({ carrierName: 'FedEx', shippingService: 'Ground Home Delivery' })

    expect(fetchLike).toHaveBeenNthCalledWith(
      2,
      'https://omsv2-staging.item.com/api/linker-oms/oas/rpc-api/mapping/shipping/execute',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer token-123' }),
        body: JSON.stringify({
          channelId: 1,
          inputConditions: {
            carrier: 'FedEx',
            shipMethod: 'Ground'
          }
        })
      })
    )
  })
})
