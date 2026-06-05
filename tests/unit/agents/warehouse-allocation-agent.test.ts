import { describe, expect, it } from 'vitest'
import { createWarehouseAllocationAgent } from '../../../src/agents/dispatch/warehouse-allocation-agent'

describe('createWarehouseAllocationAgent', () => {
  it('delegates dispatch execution and returns a normalized summary', async () => {
    const agent = createWarehouseAllocationAgent({
      dispatchSalesOrder: async () => ({
        status: 1,
        eventId: 'EVT-1',
        dispatchList: [{ dispatchNo: 'D1' }]
      })
    })

    const result = await agent.execute({
      referenceNo: 'REF-1',
      orderNo: 'SO-1',
      items: [],
      defaultRules: [],
      customRules: []
    })

    expect(result).toEqual({
      agent: 'warehouse-allocation',
      ok: true,
      summary: {
        status: 1,
        eventId: 'EVT-1',
        dispatchCount: 1
      }
    })
  })
})
