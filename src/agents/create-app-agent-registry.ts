import { createSalesOrderAgent } from './sales-order/sales-order-agent'
import { createAgentRegistry } from './base/agent-registry'

type AgentLike = {
  name: string
  description: string
  execute: (input?: unknown) => Promise<unknown>
}

type SalesOrderServiceLike = {
  querySalesOrders: (filters: { pageNo: number; pageSize: number; keyword?: string }) => Promise<{ data?: { records?: Array<Record<string, unknown>> } }>
  getSalesOrderDetail: (orderNo: string) => Promise<{ data?: Record<string, unknown> }>
  reopenSalesOrder: (orderNo: string) => Promise<unknown>
}

export function createAppAgentRegistry(deps: {
  auth: AgentLike
  salesOrderService: SalesOrderServiceLike
  omsQuery: AgentLike
}) {
  return createAgentRegistry([
    deps.auth,
    createSalesOrderAgent(deps.salesOrderService),
    deps.omsQuery
  ])
}
