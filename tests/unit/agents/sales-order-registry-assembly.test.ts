import { describe, expect, it } from 'vitest'
import { createAppAgentRegistry } from '../../../src/agents/create-app-agent-registry'

describe('createAppAgentRegistry', () => {
  it('assembles a registry that exposes the sales-order agent', async () => {
    const registry = createAppAgentRegistry({
      auth: { name: 'auth', description: 'auth', execute: async () => ({ ok: true }) },
      salesOrderService: {
        querySalesOrders: async () => ({ data: { records: [] } }),
        getSalesOrderDetail: async () => ({
          data: {
            orderNo: 'SO-300',
            status: 'OPEN',
            referenceNo: 'REF-300',
            channelSalesOrderNo: 'CH-300'
          }
        }),
        reopenSalesOrder: async () => ({ code: '200', success: true })
      },
      omsQuery: { name: 'oms-query', description: 'query', execute: async () => ({ ok: true }) }
    })

    expect(registry.get('sales-order')?.name).toBe('sales-order')

    await expect(
      registry.get('sales-order')?.execute({ type: 'detail', orderNo: 'SO-300' })
    ).resolves.toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'detail',
        orderNo: 'SO-300',
        status: 'OPEN',
        referenceNo: 'REF-300',
        channelSalesOrderNo: 'CH-300'
      },
      sections: {
        orderSummary: {
          orderNo: 'SO-300',
          status: 'OPEN',
          referenceNo: 'REF-300',
          channelSalesOrderNo: 'CH-300'
        },
        diagnosis: 'Order is currently in OPEN status.',
        availableActions: [],
        recommendedNextStep: 'Review the order details before taking further action.',
        executionResult: null
      }
    })
  })
})
