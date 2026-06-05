type DispatchService = {
  dispatchSalesOrder: (input: {
    referenceNo: string
    orderNo: string
    items: unknown[]
    defaultRules: unknown[]
    customRules: unknown[]
  }) => Promise<{ status: number; eventId: string; dispatchList: unknown[] }>
}

export function createWarehouseAllocationAgent(service: DispatchService) {
  return {
    async execute(input: {
      referenceNo: string
      orderNo: string
      items: unknown[]
      defaultRules: unknown[]
      customRules: unknown[]
    }) {
      const result = await service.dispatchSalesOrder(input)

      return {
        agent: 'warehouse-allocation',
        ok: true,
        summary: {
          status: result.status,
          eventId: result.eventId,
          dispatchCount: result.dispatchList.length
        }
      }
    }
  }
}
