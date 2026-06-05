import { describe, expect, it } from 'vitest'
import { createOmsContext } from '../../../src/config/oms-context'
import { createSalesOrderService } from '../../../src/services/sales-order/sales-order-service'

describe('createSalesOrderService', () => {
  it('queries the sales-order page endpoint with merchant-scoped filters', async () => {
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
    const service = createSalesOrderService(context, {
      get: async (path, query) => {
        captured = { path, query }
        return { data: { records: [] } }
      },
      post: async () => ({})
    })

    await service.querySalesOrders({
      pageNo: 1,
      pageSize: 20,
      keyword: 'SO-20231101',
      statuses: ['EXCEPTION']
    })

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/sale-order/page',
      query: {
        pageNo: 1,
        pageSize: 20,
        merchantNo: 'LAN0000002',
        keyword: 'SO-20231101',
        statuses: ['EXCEPTION']
      }
    })
  })

  it('loads sales-order detail by order number', async () => {
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
    const service = createSalesOrderService(context, {
      get: async (path, query) => {
        captured = { path, query }
        return { data: { orderNo: 'SO-1' } }
      },
      post: async () => ({})
    })

    await service.getSalesOrderDetail('SO-1')

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/sale-order/SO-1',
      query: undefined
    })
  })

  it('queries merchant inventory for allocation diagnosis', async () => {
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
    const service = createSalesOrderService(context, {
      get: async () => ({}),
      post: async (path, body) => {
        captured = { path, body }
        return { data: { list: [] } }
      }
    })

    await service.listInventory()

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/inventory/list',
      body: { merchantNo: 'LAN0000002' }
    })
  })

  it('checks whether an order is eligible for manual allocation', async () => {
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
    const service = createSalesOrderService(context, {
      get: async (path, query) => {
        captured = { path, query }
        return { data: true }
      },
      post: async () => ({})
    })

    await service.checkManualAllocation('SO-HAND-1')

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/dispatch/hand/check/SO-HAND-1',
      query: undefined
    })
  })

  it('fetches allocatable item lines for manual allocation', async () => {
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
    const service = createSalesOrderService(context, {
      get: async (path, query) => {
        captured = { path, query }
        return { data: { itemVOList: [] } }
      },
      post: async () => ({})
    })

    await service.getManualAllocationItems('SO-HAND-1')

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/dispatch/hand/item/SO-HAND-1',
      query: undefined
    })
  })

  it('submits a manual allocation request with warehouse and sku list', async () => {
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
    const service = createSalesOrderService(context, {
      get: async () => ({}),
      post: async (path, body) => {
        captured = { path, body }
        return { data: { success: true } }
      }
    })

    await service.manualAllocate({
      orderNo: 'SO-HAND-1',
      mode: 'SKU',
      warehouseList: [
        {
          warehouseCode: 'WH-001',
          warehouseName: 'Main Warehouse',
          skuList: [{ sku: 'DSPOST-SMALL-YELLOW', qty: 2 }]
        }
      ]
    })

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/dispatch/hand',
      body: {
        orderNo: 'SO-HAND-1',
        mode: 'SKU',
        warehouseList: [
          {
            warehouseCode: 'WH-001',
            warehouseName: 'Main Warehouse',
            skuList: [{ sku: 'DSPOST-SMALL-YELLOW', qty: 2 }]
          }
        ]
      }
    })
  })

  it('creates a purchase order with merchant scope and item list', async () => {
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
    const service = createSalesOrderService(context, {
      get: async () => ({}),
      post: async (path, body) => {
        captured = { path, body }
        return { data: { orderNo: 'PO-001' } }
      }
    })

    await service.createPurchaseOrder({
      targetWarehouseNo: 'WH-001',
      items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 2 }]
    })

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/purchase-order',
      body: {
        merchantNo: 'LAN0000002',
        phase: 2,
        source: 'AGENT',
        facilityCode: 'WH-001',
        itemList: [
          {
            sku: 'DSPOST-SMALL-YELLOW',
            qty: 2
          }
        ]
      }
    })
  })

  it('reopens a sales order by order number', async () => {
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
    const service = createSalesOrderService(context, {
      get: async () => ({}) as never,
      post: async (path, body) => {
        captured = { path, body }
        return { code: '200', success: true }
      }
    })

    await service.reopenSalesOrder('SO-REOPEN-1')

    expect(captured).toEqual({
      path: '/api/linker-oms/opc/app-api/sale-order/reopen/SO-REOPEN-1',
      body: undefined
    })
  })

  it('does not inject merchant scope into reopen requests', async () => {
    const context = createOmsContext({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'client',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'user',
      password: 'pass'
    })

    let capturedBody: unknown = 'unset'
    const service = createSalesOrderService(context, {
      get: async () => ({}) as never,
      post: async (_path, body) => {
        capturedBody = body
        return { code: '200' }
      }
    })

    await service.reopenSalesOrder('SO-REOPEN-2')

    expect(capturedBody).toBeUndefined()
  })
})
