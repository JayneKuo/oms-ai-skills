import type { OmsContext } from '../../config/oms-context'

type DispatchClient = {
  post: (path: string, body: unknown) => Promise<unknown>
}

type DispatchSalesOrderInput = {
  referenceNo: string
  orderNo: string
  items: unknown[]
  defaultRules: unknown[]
  customRules: unknown[]
}

export function createDispatchService(context: OmsContext, client: DispatchClient) {
  return {
    async dispatchSalesOrder(input: DispatchSalesOrderInput) {
      return client.post('/api/linker-oms/oas/rpc-api/dispatch/sales-order', {
        tenantId: context.tenantId,
        merchantNo: context.merchantNo,
        ...input
      })
    }
  }
}
