import type { OmsEnv } from '../config/env'
import { createSalesOrderAgent } from '../agents/sales-order/sales-order-agent'
import { createStagingBootstrap } from './bootstrap-staging'

type SalesOrderSmokeInput =
  | { type: 'query'; filters: { pageNo: number; pageSize: number; keyword?: string } }
  | { type: 'detail'; orderNo: string }
  | { type: 'diagnose-exceptions'; pageSize: number }
  | { type: 'force-allocate-without-inventory-check'; orderNo: string; targetWarehouseNo: string; confirmed?: boolean }
  | { type: 'reopen'; orderNo: string; confirmed?: boolean }
  | { type: 'get_routing_rules' }
  | { type: 'suggest_purchase_order'; items: Array<{ sku: string; quantity: number }> }
  | { type: 'release_hold'; orderNo: string }
  | { type: 'create_purchase_order'; targetWarehouseNo: string; items: Array<{ sku: string; quantity: number }> }

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export async function runStagingSalesOrderSmoke(
  env: OmsEnv,
  input: SalesOrderSmokeInput,
  fetchImpl?: FetchLike
) {
  const bootstrap = createStagingBootstrap(env, fetchImpl)
  const svc = bootstrap.services.salesOrder
  const agent = createSalesOrderAgent(svc)
  return agent.execute(input)
}
