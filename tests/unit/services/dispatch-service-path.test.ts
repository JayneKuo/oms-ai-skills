import { describe, expect, it } from 'vitest'
import { createOmsContext } from '../../../src/config/oms-context'
import { createDispatchService } from '../../../src/services/dispatch/dispatch-service'

describe('createDispatchService pathing', () => {
  it('posts sales-order dispatch requests to the staging RPC path', async () => {
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
    const service = createDispatchService(context, {
      post: async (path) => {
        capturedPath = path
        return { status: 1, eventId: 'EVT-1', dispatchList: [] }
      }
    })

    await service.dispatchSalesOrder({
      referenceNo: 'TEST-001',
      orderNo: 'SO-TEST-001',
      items: [],
      defaultRules: [],
      customRules: []
    })

    expect(capturedPath).toBe('/api/linker-oms/oas/rpc-api/dispatch/sales-order')
  })
})
