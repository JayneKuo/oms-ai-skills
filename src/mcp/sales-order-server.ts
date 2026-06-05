#!/usr/bin/env node
/**
 * Sales Order Skill — MCP Server
 *
 * 暴露销售订单相关的所有 tool，可单独使用，也可被 sales-order agent 调用。
 *
 * 启动方式：
 *   node --import=tsx skills/sales-order/mcp_server.ts
 *
 * 环境变量（必填）：
 *   OMS_BASE_URL, OMS_IAM_BASE_URL, OMS_IAM_CLIENT_ID
 *   OMS_TENANT_ID, OMS_MERCHANT_NO, OMS_USERNAME, OMS_PASSWORD
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { z } from 'zod'
import { createOmsContext } from '../../src/config/oms-context.js'
import { createStagingBootstrap } from '../../src/cli/bootstrap-staging.js'

function buildServices() {
  const context = createOmsContext({
    baseUrl: process.env.OMS_BASE_URL ?? '',
    iamBaseUrl: process.env.OMS_IAM_BASE_URL ?? '',
    iamClientId: process.env.OMS_IAM_CLIENT_ID ?? '',
    tenantId: process.env.OMS_TENANT_ID ?? '',
    merchantNo: process.env.OMS_MERCHANT_NO ?? '',
    username: process.env.OMS_USERNAME ?? '',
    password: process.env.OMS_PASSWORD ?? ''
  })
  const bootstrap = createStagingBootstrap({
    OMS_BASE_URL: context.baseUrl,
    OMS_IAM_BASE_URL: context.iamBaseUrl,
    OMS_IAM_CLIENT_ID: context.iamClientId,
    OMS_TENANT_ID: context.tenantId,
    OMS_MERCHANT_NO: context.merchantNo,
    OMS_USERNAME: context.username,
    OMS_PASSWORD: context.password
  })
  return bootstrap.services.salesOrder
}

const server = new McpServer({
  name: 'sales-order',
  version: '0.1.0'
})

server.tool(
  'query_sales_orders',
  '按关键词、状态分页查询销售订单',
  {
    pageNo: z.number().default(1),
    pageSize: z.number().default(20),
    keyword: z.string().optional(),
    statuses: z.array(z.string()).optional()
  },
  async (input) => {
    const svc = buildServices()
    const result = await svc.querySalesOrders(input)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'get_sales_order_detail',
  '获取单个销售订单的完整详情',
  { orderNo: z.string() },
  async ({ orderNo }) => {
    const svc = buildServices()
    const result = await svc.getSalesOrderDetail(orderNo)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'check_manual_allocation',
  '检查订单是否可以手动分配',
  { orderNo: z.string() },
  async ({ orderNo }) => {
    const svc = buildServices()
    const result = await svc.checkManualAllocation(orderNo)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'get_manual_allocation_items',
  '获取订单中可手动分配的商品行',
  { orderNo: z.string() },
  async ({ orderNo }) => {
    const svc = buildServices()
    const result = await svc.getManualAllocationItems(orderNo)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'manual_allocate',
  '提交手动分配请求，将订单分配到指定仓库',
  {
    orderNo: z.string(),
    mode: z.enum(['SKU', 'ORDER']).default('SKU'),
    warehouseList: z.array(z.object({
      warehouseCode: z.string(),
      warehouseName: z.string(),
      skuList: z.array(z.object({
        sku: z.string(),
        qty: z.number()
      }))
    }))
  },
  async (input) => {
    const svc = buildServices()
    const result = await svc.manualAllocate(input)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'release_hold',
  '尝试释放 ON_HOLD 状态的销售订单。释放失败时说明原因（如已全部分配、业务规则锁定等）',
  { orderNo: z.string() },
  async ({ orderNo }) => {
    const svc = buildServices()
    const releaseResult = await svc.releaseHold(orderNo)

    let noRemainingMsg = ''
    if (releaseResult.data !== true) {
      const itemsResponse = await svc.getManualAllocationItems(orderNo)
      const itemLines = (itemsResponse as { data?: { itemVOList?: Array<Record<string, unknown>> } }).data?.itemVOList ?? []
      const hasRemaining = itemLines.some((line) => Number(line.remaining ?? 0) > 0)
      if (!hasRemaining) {
        noRemainingMsg = ' All items are already fully allocated — no unfulfilled quantity remaining.'
      }
    }

    const result = {
      released: releaseResult.data === true,
      diagnosis: releaseResult.data === true
        ? `Hold on order ${orderNo} has been successfully released.`
        : `Hold on order ${orderNo} could not be released automatically.${noRemainingMsg} The hold may be locked by a business rule (e.g. payment hold, fraud check, or manual hold).`,
      recommendedNextStep: releaseResult.data === true
        ? 'Refresh the order detail to check the new status.'
        : 'Please release the hold manually in OMS or investigate the hold rule that triggered it.',
      raw: releaseResult
    }
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'create_purchase_order',
  '创建补货采购单，用于库存不足时的补货',
  {
    targetWarehouseNo: z.string(),
    items: z.array(z.object({
      sku: z.string(),
      quantity: z.number()
    }))
  },
  async (input) => {
    const svc = buildServices()
    const result = await svc.createPurchaseOrder(input)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'suggest_purchase_order',
  '根据库存和路由规则，为指定 SKU 列表推荐补货方案（仓库拆单建议），供用户确认后再执行 create_purchase_order',
  {
    items: z.array(z.object({
      sku: z.string(),
      quantity: z.number()
    }))
  },
  async ({ items }) => {
    const svc = buildServices()
    // 并行拉取库存和路由规则
    const [inventoryResponse, routingResponse] = await Promise.all([
      svc.listInventory(),
      svc.getRoutingRules()
    ])

    const inventoryData = (inventoryResponse as { data?: { list?: unknown[] } | unknown[] }).data
    const inventoryItems: Record<string, unknown>[] = Array.isArray(inventoryData)
      ? inventoryData as Record<string, unknown>[]
      : ((inventoryData as { list?: Record<string, unknown>[] })?.list ?? [])

    // 去重仓库列表
    const warehouseMap = new Map<string, { warehouseNo: string; warehouseName: string }>()
    for (const item of inventoryItems) {
      const no = String(item.warehouseNo ?? item.warehouseId ?? '')
      if (no && !warehouseMap.has(no)) {
        warehouseMap.set(no, { warehouseNo: no, warehouseName: String(item.warehouseName ?? no) })
      }
    }
    const availableWarehouses = Array.from(warehouseMap.values())

    const routingRules: Record<string, unknown>[] = Array.isArray(
      (routingResponse as { data?: unknown }).data
    )
      ? ((routingResponse as { data: Record<string, unknown>[] }).data)
      : []

    // 仓库推荐基于库存，路由规则作为上下文透传
    const defaultWarehouse = availableWarehouses[0]

    const suggestedPlan = defaultWarehouse
      ? [{ targetWarehouseNo: defaultWarehouse.warehouseNo, items }]
      : [{ targetWarehouseNo: '(select a warehouse)', items }]

    const result = {
      availableWarehouses,
      routingRules,
      suggestedPlan,
      routingRulesApplied: routingRules.length > 0,
      diagnosis: routingRules.length > 0
        ? `Found ${availableWarehouses.length} warehouse(s). Routing rules loaded (${routingRules.length} page(s)) for context. Default plan sends all items to ${suggestedPlan[0]?.targetWarehouseNo ?? '(none)'}. You can split across warehouses or pick a different one.`
        : availableWarehouses.length > 0
          ? `No routing rules found. Default plan sends all items to ${availableWarehouses[0].warehouseNo}.`
          : 'No warehouses found. Please specify a target warehouse manually.'
    }
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'get_routing_rules',
  '读取当前商户的路由规则列表 GET /routing/v2/rules',
  {},
  async () => {
    const svc = buildServices()
    const result = await svc.getRoutingRules()
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

server.tool(
  'reopen_sales_order',
  '重新开启异常状态的销售订单',
  { orderNo: z.string() },
  async ({ orderNo }) => {
    const svc = buildServices()
    const result = await svc.reopenSalesOrder(orderNo)
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  }
)

const transport = new StdioServerTransport()
await server.connect(transport)
