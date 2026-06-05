import { defineAgent } from '../base/agent-contract'

type QueryFilters = {
  pageNo: number
  pageSize: number
  keyword?: string
}

type SalesOrderAgentInput =
  | { type: 'detail'; orderNo: string }
  | { type: 'query'; filters: QueryFilters }
  | { type: 'diagnose-exceptions'; pageSize: number }
  | {
      type: 'force-allocate-without-inventory-check'
      orderNo: string
      targetWarehouseNo: string
      confirmed?: boolean
    }
  | { type: 'reopen'; orderNo: string; confirmed?: boolean }
  | { type: 'create_purchase_order'; targetWarehouseNo: string; items: Array<{ sku: string; quantity: number }> }
  | { type: 'create_purchase_order'; warehouseOrders: Array<{ targetWarehouseNo: string; items: Array<{ sku: string; quantity: number }> }> }
  | { type: 'suggest_purchase_order'; items: Array<{ sku: string; quantity: number }> }
  | { type: 'release_hold'; orderNo: string }
  | { type: 'get_routing_rules' }

type SalesOrderService = {
  querySalesOrders: (filters: QueryFilters) => Promise<{
    data?: { list?: Array<Record<string, unknown>>; records?: Array<Record<string, unknown>> }
  }>
  getSalesOrderDetail: (orderNo: string) => Promise<{ data?: Record<string, unknown> }>
  listInventory?: () => Promise<{ data?: { list?: Array<Record<string, unknown>> } | Array<Record<string, unknown>> }>
  reopenSalesOrder: (orderNo: string) => Promise<unknown>
  releaseHold?: (orderNo: string) => Promise<{ data?: unknown }>
  checkManualAllocation?: (orderNo: string) => Promise<{ data?: unknown }>
  getManualAllocationItems?: (orderNo: string) => Promise<{ data?: { itemVOList?: Array<Record<string, unknown>> } }>
  manualAllocate?: (input: {
    orderNo: string
    mode: string
    warehouseList: Array<{
      warehouseCode: string
      warehouseName: string
      skuList: Array<{ sku: string; qty: number }>
    }>
  }) => Promise<unknown>
  createPurchaseOrder?: (input: {
    targetWarehouseNo: string
    items: Array<{ sku: string; quantity: number }>
  }) => Promise<unknown>
  getRoutingRules?: () => Promise<{ data?: unknown }>
}

type Diagnosis = {
  diagnosis: string
  reasonCategory?: string
  severity?: string
  confidence?: string
  signals?: string[]
  inventorySummary?: {
    checked: boolean
    availableWarehouses: Array<Record<string, unknown>>
    missingSkus: Array<{ sku: string; requiredQty: number }>
    degraded: boolean
  }
  purchaseOrderPrompt?: {
    question: string
    requiredInputs: string[]
    suggestedItems: Array<{ sku: string; quantity: number }>
  }
  availableActions: string[]
  recommendedNextStep: string
}

function getWarehouseDisplayName(warehouse: { warehouseNo: string; warehouseName: string }) {
  return warehouse.warehouseName && warehouse.warehouseName !== warehouse.warehouseNo
    ? `${warehouse.warehouseName} (${warehouse.warehouseNo})`
    : `${warehouse.warehouseNo} (warehouse display name not returned; confirm the warehouse name before creating a PO)`
}

function summarizeRoutingRules(rules: Array<Record<string, unknown>>) {
  const activeRules = rules.flatMap((page) => {
    const ruleItems = Array.isArray(page.ruleItems) ? page.ruleItems : []
    return ruleItems
      .filter((rule): rule is Record<string, unknown> => Boolean((rule as Record<string, unknown>).switchOn))
      .map((rule) => String(rule.ruleName ?? rule.ruleId ?? 'unknown_rule'))
  })

  return {
    pageCount: rules.length,
    activeRules,
    note: 'Routing rules are dispatch strategy switches and context only; they do not by themselves prove why a sales order was assigned to a specific warehouse.'
  }
}

async function diagnoseSalesOrder(
  detail: Record<string, unknown>,
  service?: SalesOrderService
): Promise<Diagnosis> {
  const status = detail.status

  if (status !== 'EXCEPTION' && status !== 'ON_HOLD') {
    return {
      diagnosis: `Order is currently in ${String(status)} status.`,
      availableActions: [],
      recommendedNextStep: 'Review the order details before taking further action.'
    }
  }

  if (status === 'ON_HOLD') {
    // 尝试释放 hold
    if (service?.releaseHold) {
      const releaseResult = await service.releaseHold(String(detail.orderNo ?? ''))
      if (releaseResult?.data === true) {
        return {
          diagnosis: 'Order was ON_HOLD and has been successfully released.',
          availableActions: ['detail'],
          recommendedNextStep: 'Refresh the order detail to check the new status after hold release.'
        }
      }
      // 释放被拒，检查是否有未履约商品
      if (service?.getManualAllocationItems) {
        const itemsResponse = await service.getManualAllocationItems(String(detail.orderNo ?? ''))
        const itemLines = itemsResponse?.data?.itemVOList ?? []
        const hasRemaining = itemLines.some((line) => Number(line.remaining ?? 0) > 0)
        if (!hasRemaining) {
          return {
            diagnosis: 'Order is ON_HOLD and cannot be released automatically. All items are already fully allocated (no unfulfilled quantity remaining). The hold may be triggered by a business rule (e.g. payment, fraud check, or manual hold).',
            availableActions: [],
            recommendedNextStep: 'No manual allocation is needed — all items are already allocated. Please release the hold manually in OMS or investigate the hold rule that triggered it.'
          }
        }
      }
      return {
        diagnosis: 'Order is ON_HOLD and the automatic release was rejected by the system. This may be due to a business rule lock (e.g. payment hold, fraud check, or manual hold).',
        availableActions: [],
        recommendedNextStep: 'Please release the hold manually in OMS or contact the responsible team to investigate the hold reason.'
      }
    }
    return {
      diagnosis: 'Order is currently in ON_HOLD status.',
      availableActions: [],
      recommendedNextStep: 'Please release the hold manually in OMS before taking further action.'
    }
  }

  const itemLines = Array.isArray(detail.itemLines) ? detail.itemLines : []
  const unallocatedLines = itemLines.filter((line): line is Record<string, unknown> => {
    if (!line || typeof line !== 'object') {
      return false
    }

    const qty = Number(line.qty ?? 0)
    const allocatedQty = Number(line.allocatedQty ?? 0)
    return qty > allocatedQty
  })

  if (!detail.warehouseId && unallocatedLines.length > 0) {
    const affectedSkus = unallocatedLines
      .map((line) => `${String(line.sku)} (ordered ${String(line.qty)}, allocated ${String(line.allocatedQty ?? 0)})`)
      .join(', ')

    const affectedSkuList = unallocatedLines.map((line) => String(line.sku)).join(', ')
    const baseDiagnosis = {
      diagnosis: `Order is in EXCEPTION because no warehouse is assigned and ${unallocatedLines.length} item line${unallocatedLines.length > 1 ? 's have' : ' has'} unallocated quantity. Affected SKUs: ${affectedSkus}.`,
      reasonCategory: 'ALLOCATION_UNASSIGNED_WAREHOUSE',
      severity: 'high',
      confidence: 'high',
      signals: ['warehouseId is empty', `${unallocatedLines.length} item line${unallocatedLines.length > 1 ? 's have' : ' has'} qty greater than allocatedQty`]
    }

    if (service?.listInventory) {
      const inventoryResponse = await service.listInventory()
      const inventoryData = inventoryResponse.data
      const inventoryItems = Array.isArray(inventoryData) ? inventoryData : inventoryData?.list ?? []
      const availableWarehouses = unallocatedLines.flatMap((line) => {
        const sku = String(line.sku)
        const requiredQty = Number(line.qty ?? 0) - Number(line.allocatedQty ?? 0)

        return inventoryItems
          .filter((item) => String(item.sku) === sku && Number(item.availableQty ?? item.onHandQty ?? 0) >= requiredQty)
          .map((item) => ({
            sku,
            requiredQty,
            warehouseNo: item.warehouseNo ?? item.warehouseId,
            warehouseName: item.warehouseName,
            availableQty: Number(item.availableQty ?? item.onHandQty ?? 0)
          }))
      })
      const missingSkus = unallocatedLines
        .map((line) => ({
          sku: String(line.sku),
          requiredQty: Number(line.qty ?? 0) - Number(line.allocatedQty ?? 0)
        }))
        .filter((line) => !availableWarehouses.some((warehouse) => warehouse.sku === line.sku))

      if (availableWarehouses.length === 0) {
        return {
          ...baseDiagnosis,
          inventorySummary: {
            checked: true,
            availableWarehouses,
            missingSkus,
            degraded: true
          },
          availableActions: ['reopen', 'create_purchase_order_suggestion'],
          recommendedNextStep: `No warehouse currently has enough inventory for ${affectedSkuList}. Do not manual allocate yet unless the user explicitly asks to skip inventory validation. Recommend replenishing ${missingSkus[0]?.requiredQty ?? 0} units and ask whether to create a purchase order for a target warehouse.`,
          purchaseOrderPrompt: {
            question: 'Do you want me to create a purchase order to replenish inventory before allocation?',
            requiredInputs: missingSkus.flatMap((line, index) => [
              index === 0 ? 'targetWarehouseNo' : '',
              `items[${index}].sku=${line.sku}`,
              `items[${index}].quantity=${line.requiredQty}`
            ]).filter(Boolean),
            suggestedItems: missingSkus.map((line) => ({
              sku: line.sku,
              quantity: line.requiredQty
            }))
          }
        }
      }

      return {
        ...baseDiagnosis,
        inventorySummary: {
          checked: true,
          availableWarehouses,
          missingSkus,
          degraded: true
        },
        availableActions: ['reopen', 'manual_allocation_check'],
        recommendedNextStep: `Inventory exists for ${affectedSkuList}. Recommend checking allocation rules first, then manual allocate to an available warehouse if the rule path is blocked.`
      }
    }

    return {
      ...baseDiagnosis,
      availableActions: ['reopen', 'manual_allocation_check'],
      recommendedNextStep: `Check allocation rules, warehouse eligibility, and inventory for ${affectedSkuList} before confirming reopen. If allocation still fails, continue with manual allocation.`
    }
  }

  return {
    diagnosis: 'Order is currently in EXCEPTION status. No deeper exception signal was found in the order detail.',
    availableActions: ['reopen'],
    recommendedNextStep: 'Confirm reopen only if the business expects this exception order to re-enter allocation.'
  }
}

export function createSalesOrderAgent(service: SalesOrderService) {
  return defineAgent<SalesOrderAgentInput>({
    name: 'sales-order',
    description: 'Query, inspect, and reopen sales orders.',
    async execute(input) {
      if (input?.type === 'get_routing_rules') {
        if (!service.getRoutingRules) {
          return {
            agent: 'sales-order',
            ok: false,
            summary: { mode: 'get_routing_rules', result: 'unavailable' },
            sections: {
              diagnosis: 'Routing rules service is not available in this environment.',
              availableActions: [],
              recommendedNextStep: 'Check that the OMS routing API is accessible.',
              executionResult: null
            }
          }
        }
        const result = await service.getRoutingRules()
        const rules = Array.isArray((result as { data?: unknown }).data)
          ? (result as { data: unknown[] }).data
          : []
        const routingRuleSummary = summarizeRoutingRules(rules as Array<Record<string, unknown>>)
        return {
          agent: 'sales-order',
          ok: true,
          summary: { mode: 'get_routing_rules', rulePageCount: rules.length },
          sections: {
            routingRules: rules,
            routingRuleSummary,
            diagnosis: rules.length > 0
              ? `Found ${rules.length} routing rule page(s). Rules are dispatch strategy switches — they do not map SKUs to specific warehouses.`
              : 'No routing rules found for this merchant.',
            availableActions: [],
            recommendedNextStep: 'Use routing rules as context when deciding warehouse split for purchase orders.',
            executionResult: null
          }
        }
      }

      if (input?.type === 'release_hold') {
        const releaseResult = service.releaseHold
          ? await service.releaseHold(input.orderNo)
          : null

        if (releaseResult?.data === true) {
          return {
            agent: 'sales-order',
            ok: true,
            summary: { mode: 'release_hold', orderNo: input.orderNo, result: 'released' },
            sections: {
              diagnosis: `Hold on order ${input.orderNo} has been successfully released.`,
              availableActions: ['detail'],
              recommendedNextStep: 'Refresh the order detail to check the new status.',
              executionResult: releaseResult
            }
          }
        }

        // 释放失败，检查是否有未履约商品
        let noRemainingMsg = ''
        if (service.getManualAllocationItems) {
          const itemsResponse = await service.getManualAllocationItems(input.orderNo)
          const itemLines = itemsResponse?.data?.itemVOList ?? []
          const hasRemaining = itemLines.some((line) => Number(line.remaining ?? 0) > 0)
          if (!hasRemaining) {
            noRemainingMsg = ' All items are already fully allocated — no unfulfilled quantity remaining.'
          }
        }

        return {
          agent: 'sales-order',
          ok: false,
          summary: { mode: 'release_hold', orderNo: input.orderNo, result: 'rejected' },
          sections: {
            diagnosis: `Hold on order ${input.orderNo} could not be released automatically.${noRemainingMsg} The hold may be locked by a business rule (e.g. payment hold, fraud check, or manual hold).`,
            availableActions: [],
            recommendedNextStep: 'Please release the hold manually in OMS or investigate the hold rule that triggered it.',
            executionResult: releaseResult
          }
        }
      }

      if (input?.type === 'suggest_purchase_order') {
        // 并行拉取库存和路由规则
        const [inventoryResponse, routingResponse] = await Promise.all([
          service.listInventory ? service.listInventory() : Promise.resolve(null),
          service.getRoutingRules ? service.getRoutingRules() : Promise.resolve(null)
        ])

        const inventoryData = inventoryResponse?.data
        const inventoryItems = Array.isArray(inventoryData) ? inventoryData : inventoryData?.list ?? []

        // 去重仓库列表
        const warehouseMap = new Map<string, { warehouseNo: string; warehouseName: string }>()
        for (const item of inventoryItems) {
          const no = String(item.warehouseNo ?? item.warehouseId ?? '')
          if (no && !warehouseMap.has(no)) {
            warehouseMap.set(no, { warehouseNo: no, warehouseName: String(item.warehouseName ?? no) })
          }
        }
        const availableWarehouses = Array.from(warehouseMap.values())

        // 读取路由规则，作为上下文透传（规则是页签级开关，不含仓库映射，不用于自动拆单）
        const routingRules: Array<Record<string, unknown>> = Array.isArray(routingResponse?.data)
          ? (routingResponse.data as Array<Record<string, unknown>>)
          : []

        // 仓库推荐基于库存，默认发到第一个仓库
        const defaultWarehouse = availableWarehouses[0]
        const defaultWarehouseDisplay = defaultWarehouse
          ? getWarehouseDisplayName(defaultWarehouse)
          : '(select a warehouse)'

        const suggestedPlan = defaultWarehouse
          ? [{
              targetWarehouseNo: defaultWarehouse.warehouseNo,
              targetWarehouseName: defaultWarehouse.warehouseName,
              warehouseDisplayName: defaultWarehouseDisplay,
              needsWarehouseNameConfirmation: defaultWarehouse.warehouseName === defaultWarehouse.warehouseNo,
              items: input.items
            }]
          : [{ targetWarehouseNo: '(select a warehouse)', items: input.items }]

        const usedRouting = routingRules.length > 0
        const routingRuleSummary = summarizeRoutingRules(routingRules)
        const diagnosisNote = usedRouting
          ? `Found ${availableWarehouses.length} warehouse(s). Routing rules loaded (${routingRules.length} page(s)) for context. Recommended plan sends all items to ${defaultWarehouseDisplay}. You can split across warehouses or pick a different one.`
          : availableWarehouses.length > 0
            ? `No routing rules found. Recommended plan sends all items to ${defaultWarehouseDisplay}.`
            : 'No warehouses found in inventory. Please specify a target warehouse manually.'

        return {
          agent: 'sales-order',
          ok: true,
          summary: {
            mode: 'suggest_purchase_order',
            result: 'plan_ready',
            routingRulesApplied: usedRouting,
            warehouseCount: suggestedPlan.length,
            recommendedWarehouse: defaultWarehouse?.warehouseNo
          },
          sections: {
            availableWarehouses,
            routingRules,
            routingRuleSummary,
            suggestedPlan,
            diagnosis: diagnosisNote,
            availableActions: ['create_purchase_order'],
            recommendedNextStep: defaultWarehouse?.warehouseName === defaultWarehouse?.warehouseNo
              ? 'Confirm the warehouse display name for this warehouse ID, then confirm the suggested plan or adjust the split before creating a purchase order.'
              : 'Confirm the suggested plan or adjust the warehouse split, then run create_purchase_order.',
            executionResult: null
          }
        }
      }

      if (input?.type === 'create_purchase_order') {
        if (!service.createPurchaseOrder) {
          return {
            agent: 'sales-order',
            ok: false,
            summary: { mode: 'create_purchase_order', result: 'unavailable' },
            sections: {
              diagnosis: 'Purchase order creation is not available in this environment.',
              availableActions: [],
              recommendedNextStep: 'Check that the OMS purchase order API is accessible.',
              executionResult: null
            }
          }
        }

        // 多仓拆单：warehouseOrders 字段
        if ('warehouseOrders' in input) {
          const results = await Promise.all(
            input.warehouseOrders.map((order) =>
              service.createPurchaseOrder!({
                targetWarehouseNo: order.targetWarehouseNo,
                items: order.items
              })
            )
          )
          return {
            agent: 'sales-order',
            ok: true,
            summary: {
              mode: 'create_purchase_order',
              warehouseCount: input.warehouseOrders.length,
              result: 'submitted'
            },
            sections: {
              diagnosis: `Created ${input.warehouseOrders.length} purchase order${input.warehouseOrders.length > 1 ? 's' : ''} across ${input.warehouseOrders.length} warehouse${input.warehouseOrders.length > 1 ? 's' : ''}.`,
              availableActions: ['detail'],
              recommendedNextStep: 'Monitor purchase order fulfillment, then retry allocation once inventory arrives.',
              executionResult: results
            }
          }
        }

        // 单仓：targetWarehouseNo + items
        const result = await service.createPurchaseOrder({
          targetWarehouseNo: input.targetWarehouseNo,
          items: input.items
        })
        return {
          agent: 'sales-order',
          ok: true,
          summary: {
            mode: 'create_purchase_order',
            targetWarehouseNo: input.targetWarehouseNo,
            result: 'submitted'
          },
          sections: {
            diagnosis: `Purchase order created for warehouse ${input.targetWarehouseNo} with ${input.items.length} SKU(s).`,
            availableActions: ['detail'],
            recommendedNextStep: 'Monitor purchase order fulfillment, then retry allocation once inventory arrives.',
            executionResult: result
          }
        }
      }

      if (input?.type === 'detail') {
        const response = await service.getSalesOrderDetail(input.orderNo)
        const detail = response.data ?? {}
        const status = detail.status
        const diagnosis = await diagnoseSalesOrder(detail, service)

        return {
          agent: 'sales-order',
          ok: true,
          summary: {
            mode: 'detail',
            orderNo: detail.orderNo,
            status,
            referenceNo: detail.referenceNo,
            channelSalesOrderNo: detail.channelSalesOrderNo
          },
          sections: {
            orderSummary: {
              orderNo: detail.orderNo,
              status,
              referenceNo: detail.referenceNo,
              channelSalesOrderNo: detail.channelSalesOrderNo
            },
            diagnosis: diagnosis.diagnosis,
            reasonCategory: diagnosis.reasonCategory,
            severity: diagnosis.severity,
            confidence: diagnosis.confidence,
            signals: diagnosis.signals,
            inventorySummary: diagnosis.inventorySummary,
            availableActions: diagnosis.availableActions,
            recommendedNextStep: diagnosis.recommendedNextStep,
            purchaseOrderPrompt: diagnosis.purchaseOrderPrompt,
            executionResult: null
          }
        }
      }

      if (input?.type === 'query') {
        const response = await service.querySalesOrders(input.filters)
        const records = response.data?.records ?? response.data?.list ?? []
        const orders = records.map((record) => ({
          orderNo: record.orderNo,
          status: record.status
        }))

        return {
          agent: 'sales-order',
          ok: true,
          summary: {
            mode: 'query',
            totalRecords: records.length,
            orders
          },
          sections: {
            orderSummary: {
              totalRecords: records.length,
              orders
            },
            diagnosis: `Found ${records.length} matching sales orders.`,
            availableActions: records.length > 0 ? ['detail'] : [],
            recommendedNextStep:
              records.length > 0
                ? 'Review an order from the result set for detailed diagnosis or action.'
                : 'Adjust the query filters and try again.',
            executionResult: null
          }
        }
      }

      if (input?.type === 'force-allocate-without-inventory-check') {
        if (!input.confirmed) {
          return {
            agent: 'sales-order',
            ok: false,
            summary: {
              mode: 'force-allocate-without-inventory-check',
              orderNo: input.orderNo,
              targetWarehouseNo: input.targetWarehouseNo,
              result: 'confirmation_required'
            },
            sections: {
              diagnosis:
                'Forced allocation bypasses inventory validation. This will manually assign the order to the target warehouse regardless of stock levels.',
              availableActions: ['confirm_force_allocate'],
              recommendedNextStep: `Run force-allocate again with confirmed=true to proceed with manual allocation of ${input.orderNo} to warehouse ${input.targetWarehouseNo}. Only do this if you are certain inventory will be available or the business explicitly accepts the risk.`,
              executionResult: null
            }
          }
        }

        // confirmed=true: check eligibility then execute manual allocation
        const eligible = service.checkManualAllocation
          ? await service.checkManualAllocation(input.orderNo)
          : null
        if (eligible?.data === false) {
          return {
            agent: 'sales-order',
            ok: false,
            summary: {
              mode: 'force-allocate-without-inventory-check',
              orderNo: input.orderNo,
              targetWarehouseNo: input.targetWarehouseNo,
              result: 'not_eligible'
            },
            sections: {
              diagnosis: `Order ${input.orderNo} is not eligible for manual allocation.`,
              availableActions: [],
              recommendedNextStep: 'Review the order status and allocation rules before retrying.',
              executionResult: null
            }
          }
        }

        const itemsResponse = service.getManualAllocationItems
          ? await service.getManualAllocationItems(input.orderNo)
          : null
        const itemLines = itemsResponse?.data?.itemVOList ?? []
        const skuList = itemLines
          .filter((line) => Number(line.remaining ?? line.qty ?? line.unallocatedQty ?? 0) > 0)
          .map((line) => ({
            sku: String(line.sku),
            qty: Number(line.remaining ?? line.qty ?? line.unallocatedQty ?? 0)
          }))

        if (skuList.length === 0) {
          return {
            agent: 'sales-order',
            ok: false,
            summary: {
              mode: 'force-allocate-without-inventory-check',
              orderNo: input.orderNo,
              targetWarehouseNo: input.targetWarehouseNo,
              result: 'nothing_to_allocate'
            },
            sections: {
              diagnosis: `All items in order ${input.orderNo} are already fully allocated. There are no unfulfilled quantities remaining — manual allocation is not needed.`,
              availableActions: [],
              recommendedNextStep: 'No action required for allocation. If the order is still stuck, check the order status or hold reason.',
              executionResult: null
            }
          }
        }

        const executionResult = service.manualAllocate
          ? await service.manualAllocate({
              orderNo: input.orderNo,
              mode: 'SKU',
              warehouseList: [
                {
                  warehouseCode: input.targetWarehouseNo,
                  warehouseName: input.targetWarehouseNo,
                  skuList
                }
              ]
            })
          : null

        return {
          agent: 'sales-order',
          ok: true,
          summary: {
            mode: 'force-allocate-without-inventory-check',
            orderNo: input.orderNo,
            targetWarehouseNo: input.targetWarehouseNo,
            result: 'submitted'
          },
          sections: {
            diagnosis: `Manual allocation submitted for ${input.orderNo} to warehouse ${input.targetWarehouseNo}.`,
            availableActions: ['detail'],
            recommendedNextStep: 'Refresh the order detail to verify allocation status.',
            executionResult
          }
        }
      }

      if (input?.type === 'diagnose-exceptions') {
        const response = await service.querySalesOrders({
          pageNo: 1,
          pageSize: input.pageSize,
          statuses: ['EXCEPTION']
        } as QueryFilters)
        const records = response.data?.records ?? response.data?.list ?? []
        const diagnoses = await Promise.all(
          records.map(async (record) => {
            const orderNo = String(record.orderNo)
            const listedStatus = record.status
            const detailResponse = await service.getSalesOrderDetail(orderNo)
            const detail = detailResponse.data ?? {}
            const currentStatus = detail.status
            const statusChangedFromException = listedStatus === 'EXCEPTION' && currentStatus !== 'EXCEPTION'
            const diagnosis = statusChangedFromException
              ? {
                  diagnosis: `This order appeared in the EXCEPTION query result, but its current detail status is ${String(currentStatus)}. It may have already moved out of exception after the list was generated.`,
                  reasonCategory: 'STATUS_CHANGED_FROM_EXCEPTION',
                  severity: 'low',
                  confidence: 'high',
                  signals: [`list status was ${String(listedStatus)}`, `detail status is ${String(currentStatus)}`],
                  availableActions: ['detail'],
                  recommendedNextStep: 'Refresh the order detail and do not reopen or manually allocate unless the latest status becomes eligible again.'
                }
              : await diagnoseSalesOrder(detail, service)

            return {
              orderNo: detail.orderNo,
              status: currentStatus,
              ...(listedStatus !== currentStatus ? { listedStatus } : {}),
              referenceNo: detail.referenceNo,
              channelSalesOrderNo: detail.channelSalesOrderNo,
              diagnosis: diagnosis.diagnosis,
              reasonCategory: diagnosis.reasonCategory,
              severity: diagnosis.severity,
              confidence: diagnosis.confidence,
              signals: diagnosis.signals,
              ...(diagnosis.inventorySummary ? { inventorySummary: diagnosis.inventorySummary } : {}),
              availableActions: diagnosis.availableActions,
              recommendedNextStep: diagnosis.recommendedNextStep
            }
          })
        )
        const reopenCandidates = diagnoses
          .filter((diagnosis) => diagnosis.availableActions.includes('reopen'))
          .map((diagnosis) => String(diagnosis.orderNo))
        const manualAllocationCandidates = diagnoses
          .filter((diagnosis) => diagnosis.availableActions.includes('manual_allocation_check'))
          .map((diagnosis) => String(diagnosis.orderNo))
        const blocked = diagnoses
          .filter((diagnosis) => diagnosis.status === 'EXCEPTION' && diagnosis.availableActions.length === 0)
          .map((diagnosis) => String(diagnosis.orderNo))
        const statusChanged = diagnoses
          .filter((diagnosis) => diagnosis.reasonCategory === 'STATUS_CHANGED_FROM_EXCEPTION')
          .map((diagnosis) => String(diagnosis.orderNo))
        const actionPlan: {
          reopenCandidates: string[]
          manualAllocationCandidates: string[]
          blocked: string[]
          statusChanged?: string[]
        } = {
          reopenCandidates,
          manualAllocationCandidates,
          blocked
        }
        if (statusChanged.length > 0) {
          actionPlan.statusChanged = statusChanged
        }

        return {
          agent: 'sales-order',
          ok: true,
          summary: {
            mode: 'diagnose-exceptions',
            totalRecords: diagnoses.length,
            actionPlan
          },
          sections: {
            diagnoses,
            recommendedNextStep:
              statusChanged.length > 0
                ? 'Some orders have already moved out of EXCEPTION. Refresh those order details and only continue action on orders that are still eligible.'
                : 'Review the action plan, then confirm reopen only for eligible orders or continue into manual allocation checks for inventory/warehouse failures.',
            executionResult: null
          }
        }
      }

      const orderNo = input?.orderNo

      if (!input?.confirmed) {
        return {
          agent: 'sales-order',
          ok: false,
          summary: {
            mode: 'reopen',
            orderNo,
            result: 'confirmation_required'
          },
          sections: {
            diagnosis: 'Reopen changes the sales order state and requires explicit confirmation.',
            availableActions: ['confirm_reopen'],
            recommendedNextStep: 'Run reopen again with confirmed=true after verifying the order is eligible.',
            executionResult: null
          }
        }
      }

      const detailResponse = await service.getSalesOrderDetail(orderNo)
      const detail = detailResponse.data ?? {}
      const status = detail.status

      if (status !== 'EXCEPTION') {
        return {
          agent: 'sales-order',
          ok: false,
          summary: {
            mode: 'reopen',
            orderNo,
            status,
            result: 'not_eligible'
          },
          sections: {
            diagnosis: `Order is currently in ${String(status)} status and is not eligible for reopen.`,
            availableActions: [],
            recommendedNextStep: 'Do not reopen this order. Review the order detail for the next valid operation.',
            executionResult: null
          }
        }
      }

      const executionResult = await service.reopenSalesOrder(orderNo)

      return {
        agent: 'sales-order',
        ok: true,
        summary: {
          mode: 'reopen',
          orderNo,
          status,
          result: 'submitted'
        },
        sections: {
          diagnosis: 'Order was eligible for reopen because it was in EXCEPTION status.',
          availableActions: ['detail'],
          recommendedNextStep: 'Refresh the order detail to verify the latest status after reopen.',
          executionResult
        }
      }
    }
  })
}
