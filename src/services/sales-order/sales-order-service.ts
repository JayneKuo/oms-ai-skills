import type { OmsContext } from '../../config/oms-context'

type SalesOrderClient = {
  get: (path: string, query?: Record<string, unknown>) => Promise<unknown>
  post: (path: string, body: unknown) => Promise<unknown>
}

type QuerySalesOrdersInput = {
  pageNo: number
  pageSize: number
  keyword?: string
  statuses?: string[]
}

export function createSalesOrderService(context: OmsContext, client: SalesOrderClient) {
  return {
    async querySalesOrders(input: QuerySalesOrdersInput) {
      return client.get('/api/linker-oms/opc/app-api/sale-order/page', {
        ...input,
        merchantNo: context.merchantNo
      })
    },
    async getSalesOrderDetail(orderNo: string) {
      return client.get(`/api/linker-oms/opc/app-api/sale-order/${orderNo}`)
    },
    async listInventory() {
      return client.post('/api/linker-oms/opc/app-api/inventory/list', {
        merchantNo: context.merchantNo
      })
    },
    async reopenSalesOrder(orderNo: string) {
      return client.post(`/api/linker-oms/opc/app-api/sale-order/reopen/${orderNo}`, undefined)
    },
    async releaseHold(orderNo: string) {
      return client.post(`/api/linker-oms/opc/app-api/order-hold/release?orderNo=${encodeURIComponent(orderNo)}`, undefined)
    },
    async checkManualAllocation(orderNo: string) {
      return client.get(`/api/linker-oms/opc/app-api/dispatch/hand/check/${orderNo}`)
    },
    async getManualAllocationItems(orderNo: string) {
      return client.get(`/api/linker-oms/opc/app-api/dispatch/hand/item/${orderNo}`)
    },
    async manualAllocate(input: {
      orderNo: string
      mode?: string
      dispatchType?: string
      warehouseList?: Array<{
        warehouseCode: string
        warehouseName: string
        skuList: Array<{ sku: string; qty: number }>
      }>
      warehouseDTOList?: Array<{
        warehouseName: string
        accountingCode?: string
        itemDTOList?: Array<{ sku: string; qty: number; uom?: string }>
      }>
      itemDTOList?: Array<{ sku: string; qty: number; uom?: string }>
      remark?: string
    }) {
      return client.post('/api/linker-oms/opc/app-api/dispatch/hand', input)
    },
    async createPurchaseOrder(input: {
      targetWarehouseNo: string
      items: Array<{ sku: string; quantity: number }>
    }) {
      return client.post('/api/linker-oms/opc/app-api/purchase-order', {
        merchantNo: context.merchantNo,
        phase: 2,
        source: 'AGENT',
        facilityCode: input.targetWarehouseNo,
        itemList: input.items.map((item) => ({ sku: item.sku, qty: item.quantity }))
      })
    },
    async getRoutingRules() {
      return client.get('/api/linker-oms/opc/app-api/routing/v2/rules', { merchantNo: context.merchantNo })
    }
  }
}
