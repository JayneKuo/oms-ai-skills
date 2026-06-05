import { describe, expect, it } from 'vitest'
import { createOmsContext } from '../../../src/config/oms-context'
import { createDispatchService } from '../../../src/services/dispatch/dispatch-service'

describe('createDispatchService', () => {
  it('adds tenant and merchant context to sales-order dispatch payloads', async () => {
    const context = createOmsContext({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'client',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'user',
      password: 'pass'
    })

    let captured: unknown
    const service = createDispatchService(context, {
      post: async (_path, body) => {
        captured = body
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

    expect(captured).toEqual({
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      referenceNo: 'TEST-001',
      orderNo: 'SO-TEST-001',
      items: [],
      defaultRules: [],
      customRules: []
    })
  })
})
