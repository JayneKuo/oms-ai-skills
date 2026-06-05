import { describe, expect, it } from 'vitest'
import { createSalesOrderAgent } from '../../../src/agents/sales-order/sales-order-agent'

describe('createSalesOrderAgent output contract', () => {
  it('returns publishable detail sections for exception diagnosis', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({
        data: {
          orderNo: 'SO-400',
          status: 'EXCEPTION',
          referenceNo: 'REF-400',
          channelSalesOrderNo: 'CH-400'
        }
      }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({ type: 'detail', orderNo: 'SO-400' })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'detail',
        orderNo: 'SO-400',
        status: 'EXCEPTION',
        referenceNo: 'REF-400',
        channelSalesOrderNo: 'CH-400'
      },
      sections: {
        orderSummary: {
          orderNo: 'SO-400',
          status: 'EXCEPTION',
          referenceNo: 'REF-400',
          channelSalesOrderNo: 'CH-400'
        },
        diagnosis: 'Order is currently in EXCEPTION status. No deeper exception signal was found in the order detail.',
        availableActions: ['reopen'],
        recommendedNextStep: 'Confirm reopen only if the business expects this exception order to re-enter allocation.',
        executionResult: null
      }
    })
  })
})
