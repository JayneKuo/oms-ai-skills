import { describe, expect, it } from 'vitest'
import { createOmsContext } from '../../../src/config/oms-context'
import { createMappingService } from '../../../src/services/mapping/mapping-service'

describe('createMappingService pathing', () => {
  it('posts shipping mapping requests to the staging RPC path', async () => {
    const context = createOmsContext({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'client',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'user',
      password: 'pass'
    })

    let capturedPath: string | undefined
    const service = createMappingService(context, {
      get: async () => [],
      post: async (path) => {
        capturedPath = path
        return { carrierName: 'FedEx', shippingService: 'Ground Home Delivery' }
      }
    })

    await service.executeShippingMapping({
      channelId: 1,
      inputConditions: {
        carrier: 'FedEx',
        shipMethod: 'Ground'
      }
    })

    expect(capturedPath).toBe('/api/linker-oms/oas/rpc-api/mapping/shipping/execute')
  })
})
