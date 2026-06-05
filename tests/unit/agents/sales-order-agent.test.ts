import { describe, expect, it } from 'vitest'
import { createSalesOrderAgent } from '../../../src/agents/sales-order/sales-order-agent'

describe('createSalesOrderAgent', () => {
  it('diagnoses a batch of exception orders with detail-level reasons', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({
        data: {
          list: [
            { orderNo: 'SO-EX-1', status: 'EXCEPTION' },
            { orderNo: 'SO-EX-2', status: 'EXCEPTION' }
          ]
        }
      }),
      getSalesOrderDetail: async (orderNo: string) => ({
        data: {
          orderNo,
          status: 'EXCEPTION',
          referenceNo: `${orderNo}-REF`,
          channelSalesOrderNo: `${orderNo}-CH`,
          warehouseId: null,
          itemLines: [
            {
              sku: `${orderNo}-SKU`,
              qty: 3,
              allocatedQty: 1
            }
          ]
        }
      }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'diagnose-exceptions',
      pageSize: 2
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'diagnose-exceptions',
        totalRecords: 2,
        actionPlan: {
          reopenCandidates: ['SO-EX-1', 'SO-EX-2'],
          manualAllocationCandidates: ['SO-EX-1', 'SO-EX-2'],
          blocked: []
        }
      },
      sections: {
        diagnoses: [
          {
            orderNo: 'SO-EX-1',
            status: 'EXCEPTION',
            referenceNo: 'SO-EX-1-REF',
            channelSalesOrderNo: 'SO-EX-1-CH',
            diagnosis:
              'Order is in EXCEPTION because no warehouse is assigned and 1 item line has unallocated quantity. Affected SKUs: SO-EX-1-SKU (ordered 3, allocated 1).',
            reasonCategory: 'ALLOCATION_UNASSIGNED_WAREHOUSE',
            severity: 'high',
            confidence: 'high',
            signals: ['warehouseId is empty', '1 item line has qty greater than allocatedQty'],
            availableActions: ['reopen', 'manual_allocation_check'],
            recommendedNextStep:
              'Check allocation rules, warehouse eligibility, and inventory for SO-EX-1-SKU before confirming reopen. If allocation still fails, continue with manual allocation.'
          },
          {
            orderNo: 'SO-EX-2',
            status: 'EXCEPTION',
            referenceNo: 'SO-EX-2-REF',
            channelSalesOrderNo: 'SO-EX-2-CH',
            diagnosis:
              'Order is in EXCEPTION because no warehouse is assigned and 1 item line has unallocated quantity. Affected SKUs: SO-EX-2-SKU (ordered 3, allocated 1).',
            reasonCategory: 'ALLOCATION_UNASSIGNED_WAREHOUSE',
            severity: 'high',
            confidence: 'high',
            signals: ['warehouseId is empty', '1 item line has qty greater than allocatedQty'],
            availableActions: ['reopen', 'manual_allocation_check'],
            recommendedNextStep:
              'Check allocation rules, warehouse eligibility, and inventory for SO-EX-2-SKU before confirming reopen. If allocation still fails, continue with manual allocation.'
          }
        ],
        recommendedNextStep:
          'Review the action plan, then confirm reopen only for eligible orders or continue into manual allocation checks for inventory/warehouse failures.',
        executionResult: null
      }
    })
  })

  it('returns a normalized business summary for sales-order detail lookup', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async (orderNo: string) => ({
        data: {
          orderNo,
          status: 'EXCEPTION',
          referenceNo: 'REF-100',
          channelSalesOrderNo: 'CH-100'
        }
      }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'detail',
      orderNo: 'SO-100'
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'detail',
        orderNo: 'SO-100',
        status: 'EXCEPTION',
        referenceNo: 'REF-100',
        channelSalesOrderNo: 'CH-100'
      },
      sections: {
        orderSummary: {
          orderNo: 'SO-100',
          status: 'EXCEPTION',
          referenceNo: 'REF-100',
          channelSalesOrderNo: 'CH-100'
        },
        diagnosis: 'Order is currently in EXCEPTION status. No deeper exception signal was found in the order detail.',
        availableActions: ['reopen'],
        recommendedNextStep: 'Confirm reopen only if the business expects this exception order to re-enter allocation.',
        executionResult: null
      }
    })
  })

  it('explains exception orders caused by unallocated item lines', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({
        data: {
          orderNo: 'SO-ALLOC-1',
          status: 'EXCEPTION',
          referenceNo: 'REF-ALLOC-1',
          channelSalesOrderNo: 'CH-ALLOC-1',
          warehouseId: null,
          qty: 2,
          itemLines: [
            {
              sku: 'DSPOST-SMALL-YELLOW',
              qty: 2,
              allocatedQty: 0
            }
          ]
        }
      }),
      listInventory: async () => ({ data: { list: [] } }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'detail',
      orderNo: 'SO-ALLOC-1'
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'detail',
        orderNo: 'SO-ALLOC-1',
        status: 'EXCEPTION',
        referenceNo: 'REF-ALLOC-1',
        channelSalesOrderNo: 'CH-ALLOC-1'
      },
      sections: {
        orderSummary: {
          orderNo: 'SO-ALLOC-1',
          status: 'EXCEPTION',
          referenceNo: 'REF-ALLOC-1',
          channelSalesOrderNo: 'CH-ALLOC-1'
        },
        diagnosis:
          'Order is in EXCEPTION because no warehouse is assigned and 1 item line has unallocated quantity. Affected SKUs: DSPOST-SMALL-YELLOW (ordered 2, allocated 0).',
        reasonCategory: 'ALLOCATION_UNASSIGNED_WAREHOUSE',
        severity: 'high',
        confidence: 'high',
        signals: ['warehouseId is empty', '1 item line has qty greater than allocatedQty'],
        inventorySummary: {
          checked: true,
          availableWarehouses: [],
          missingSkus: [{ sku: 'DSPOST-SMALL-YELLOW', requiredQty: 2 }],
          degraded: true
        },
        availableActions: ['reopen', 'create_purchase_order_suggestion'],
        recommendedNextStep:
          'No warehouse currently has enough inventory for DSPOST-SMALL-YELLOW. Do not manual allocate yet unless the user explicitly asks to skip inventory validation. Recommend replenishing 2 units and ask whether to create a purchase order for a target warehouse.',
        purchaseOrderPrompt: {
          question: 'Do you want me to create a purchase order to replenish inventory before allocation?',
          requiredInputs: [
            'targetWarehouseNo',
            'items[0].sku=DSPOST-SMALL-YELLOW',
            'items[0].quantity=2'
          ],
          suggestedItems: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 2 }]
        },
        executionResult: null
      }
    })
  })

  it('requires confirmation before forced allocation when inventory validation is skipped', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'force-allocate-without-inventory-check',
      orderNo: 'SO-ALLOC-1',
      targetWarehouseNo: 'WH-001'
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: false,
      summary: {
        mode: 'force-allocate-without-inventory-check',
        orderNo: 'SO-ALLOC-1',
        targetWarehouseNo: 'WH-001',
        result: 'confirmation_required'
      },
      sections: {
        diagnosis:
          'Forced allocation bypasses inventory validation. This will manually assign the order to the target warehouse regardless of stock levels.',
        availableActions: ['confirm_force_allocate'],
        recommendedNextStep:
          'Run force-allocate again with confirmed=true to proceed with manual allocation of SO-ALLOC-1 to warehouse WH-001. Only do this if you are certain inventory will be available or the business explicitly accepts the risk.',
        executionResult: null
      }
    })
  })

  it('returns a list summary for sales-order query', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({
        data: {
          records: [
            { orderNo: 'SO-1', status: 'OPEN' },
            { orderNo: 'SO-2', status: 'EXCEPTION' }
          ]
        }
      }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'query',
      filters: {
        pageNo: 1,
        pageSize: 20,
        keyword: 'SO'
      }
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'query',
        totalRecords: 2,
        orders: [
          { orderNo: 'SO-1', status: 'OPEN' },
          { orderNo: 'SO-2', status: 'EXCEPTION' }
        ]
      },
      sections: {
        orderSummary: {
          totalRecords: 2,
          orders: [
            { orderNo: 'SO-1', status: 'OPEN' },
            { orderNo: 'SO-2', status: 'EXCEPTION' }
          ]
        },
        diagnosis: 'Found 2 matching sales orders.',
        availableActions: ['detail'],
        recommendedNextStep: 'Review an order from the result set for detailed diagnosis or action.',
        executionResult: null
      }
    })
  })

  it('separates exception query records that already moved to another status', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({
        data: {
          list: [{ orderNo: 'SO-MOVED-1', status: 'EXCEPTION' }]
        }
      }),
      getSalesOrderDetail: async () => ({
        data: {
          orderNo: 'SO-MOVED-1',
          status: 'WAREHOUSE_PROCESSING',
          referenceNo: 'REF-MOVED',
          channelSalesOrderNo: 'CH-MOVED'
        }
      }),
      reopenSalesOrder: async () => ({})
    })

    const result = await agent.execute({ type: 'diagnose-exceptions', pageSize: 1 })

    expect(result).toMatchObject({
      summary: {
        mode: 'diagnose-exceptions',
        actionPlan: {
          reopenCandidates: [],
          manualAllocationCandidates: [],
          blocked: [],
          statusChanged: ['SO-MOVED-1']
        }
      },
      sections: {
        diagnoses: [
          expect.objectContaining({
            orderNo: 'SO-MOVED-1',
            listedStatus: 'EXCEPTION',
            status: 'WAREHOUSE_PROCESSING',
            reasonCategory: 'STATUS_CHANGED_FROM_EXCEPTION',
            availableActions: ['detail']
          })
        ],
        recommendedNextStep: expect.stringContaining('moved out of EXCEPTION')
      }
    })
  })

  it('returns a list summary for live sales-order page responses that use data.list', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({
        data: {
          list: [
            { orderNo: 'SO01385247', status: 'WAREHOUSE_PROCESSING' },
            { orderNo: 'SO01385246', status: 'ON_HOLD' }
          ]
        }
      }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'query',
      filters: {
        pageNo: 1,
        pageSize: 5
      }
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'query',
        totalRecords: 2,
        orders: [
          { orderNo: 'SO01385247', status: 'WAREHOUSE_PROCESSING' },
          { orderNo: 'SO01385246', status: 'ON_HOLD' }
        ]
      },
      sections: {
        orderSummary: {
          totalRecords: 2,
          orders: [
            { orderNo: 'SO01385247', status: 'WAREHOUSE_PROCESSING' },
            { orderNo: 'SO01385246', status: 'ON_HOLD' }
          ]
        },
        diagnosis: 'Found 2 matching sales orders.',
        availableActions: ['detail'],
        recommendedNextStep: 'Review an order from the result set for detailed diagnosis or action.',
        executionResult: null
      }
    })
  })

  it('requires explicit confirmation before reopening a sales order', async () => {
    let called = false
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => {
        called = true
        return { code: '200', success: true }
      }
    })

    const result = await agent.execute({
      type: 'reopen',
      orderNo: 'SO-200'
    })

    expect(called).toBe(false)
    expect(result).toEqual({
      agent: 'sales-order',
      ok: false,
      summary: {
        mode: 'reopen',
        orderNo: 'SO-200',
        result: 'confirmation_required'
      },
      sections: {
        diagnosis: 'Reopen changes the sales order state and requires explicit confirmation.',
        availableActions: ['confirm_reopen'],
        recommendedNextStep: 'Run reopen again with confirmed=true after verifying the order is eligible.',
        executionResult: null
      }
    })
  })

  it('blocks confirmed reopen when the current order status is not EXCEPTION', async () => {
    let called = false
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({
        data: {
          orderNo: 'SO-200',
          status: 'ALLOCATED'
        }
      }),
      reopenSalesOrder: async () => {
        called = true
        return { code: '200', success: true }
      }
    })

    const result = await agent.execute({
      type: 'reopen',
      orderNo: 'SO-200',
      confirmed: true
    })

    expect(called).toBe(false)
    expect(result).toEqual({
      agent: 'sales-order',
      ok: false,
      summary: {
        mode: 'reopen',
        orderNo: 'SO-200',
        status: 'ALLOCATED',
        result: 'not_eligible'
      },
      sections: {
        diagnosis: 'Order is currently in ALLOCATED status and is not eligible for reopen.',
        availableActions: [],
        recommendedNextStep: 'Do not reopen this order. Review the order detail for the next valid operation.',
        executionResult: null
      }
    })
  })

  it('returns an execution summary for confirmed reopen action on an EXCEPTION order', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({
        data: {
          orderNo: 'SO-200',
          status: 'EXCEPTION'
        }
      }),
      reopenSalesOrder: async () => ({ code: '200', success: true })
    })

    const result = await agent.execute({
      type: 'reopen',
      orderNo: 'SO-200',
      confirmed: true
    })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'reopen',
        orderNo: 'SO-200',
        status: 'EXCEPTION',
        result: 'submitted'
      },
      sections: {
        diagnosis: 'Order was eligible for reopen because it was in EXCEPTION status.',
        availableActions: ['detail'],
        recommendedNextStep: 'Refresh the order detail to verify the latest status after reopen.',
        executionResult: { code: '200', success: true }
      }
    })
  })

  it('creates a purchase order to a single target warehouse when user confirms', async () => {
    let captured: unknown
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      createPurchaseOrder: async (input) => {
        captured = input
        return { data: { orderNo: 'PO-001' } }
      }
    })

    const result = await agent.execute({
      type: 'create_purchase_order',
      targetWarehouseNo: 'WH-001',
      items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 2 }]
    })

    expect(captured).toEqual({
      targetWarehouseNo: 'WH-001',
      items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 2 }]
    })
    expect(result).toMatchObject({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'create_purchase_order',
        targetWarehouseNo: 'WH-001',
        result: 'submitted'
      }
    })
  })

  it('creates purchase orders across multiple warehouses when user splits a sku', async () => {
    const captured: unknown[] = []
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      createPurchaseOrder: async (input) => {
        captured.push(input)
        return { data: { orderNo: `PO-${captured.length}` } }
      }
    })

    const result = await agent.execute({
      type: 'create_purchase_order',
      warehouseOrders: [
        { targetWarehouseNo: 'WH-001', items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 1 }] },
        { targetWarehouseNo: 'WH-002', items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 1 }] }
      ]
    })

    expect(captured).toHaveLength(2)
    expect(captured[0]).toEqual({ targetWarehouseNo: 'WH-001', items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 1 }] })
    expect(captured[1]).toEqual({ targetWarehouseNo: 'WH-002', items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 1 }] })
    expect(result).toMatchObject({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'create_purchase_order',
        warehouseCount: 2,
        result: 'submitted'
      }
    })
  })

  it('suggests warehouse allocation plan from inventory list before creating purchase order', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      listInventory: async () => ({
        data: {
          list: [
            { warehouseNo: 'WH-001', warehouseName: 'Main Warehouse', sku: 'DSPOST-SMALL-YELLOW', availableQty: 0 },
            { warehouseNo: 'WH-002', warehouseName: 'East Warehouse', sku: 'DSPOST-SMALL-YELLOW', availableQty: 0 }
          ]
        }
      })
    })

    const result = await agent.execute({
      type: 'suggest_purchase_order',
      items: [{ sku: 'DSPOST-SMALL-YELLOW', quantity: 2 }]
    })

    expect(result).toMatchObject({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'suggest_purchase_order',
        result: 'plan_ready'
      },
      sections: expect.objectContaining({
        availableWarehouses: expect.arrayContaining([
          expect.objectContaining({ warehouseNo: 'WH-001' }),
          expect.objectContaining({ warehouseNo: 'WH-002' })
        ]),
        suggestedPlan: [
          expect.objectContaining({
            targetWarehouseNo: 'WH-001',
            targetWarehouseName: 'Main Warehouse',
            warehouseDisplayName: 'Main Warehouse (WH-001)',
            needsWarehouseNameConfirmation: false
          })
        ],
        availableActions: ['create_purchase_order'],
        recommendedNextStep: expect.any(String)
      })
    })
  })

  it('asks users to confirm warehouse name when inventory only returns a warehouse id', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      listInventory: async () => ({
        data: {
          list: [{ warehouseNo: 'WH-ID-ONLY', sku: 'SKU-A', availableQty: 0 }]
        }
      })
    })

    const result = await agent.execute({
      type: 'suggest_purchase_order',
      items: [{ sku: 'SKU-A', quantity: 5 }]
    })

    expect(result).toMatchObject({
      summary: expect.objectContaining({
        recommendedWarehouse: 'WH-ID-ONLY'
      }),
      sections: expect.objectContaining({
        suggestedPlan: [
          expect.objectContaining({
            targetWarehouseNo: 'WH-ID-ONLY',
            targetWarehouseName: 'WH-ID-ONLY',
            needsWarehouseNameConfirmation: true
          })
        ],
        diagnosis: expect.stringContaining('warehouse display name not returned'),
        recommendedNextStep: expect.stringContaining('Confirm the warehouse display name')
      })
    })
  })

  it('releases hold successfully when service returns true', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      releaseHold: async () => ({ data: true })
    })

    const result = await agent.execute({ type: 'release_hold', orderNo: 'SO-HOLD-1' })

    expect(result).toEqual({
      agent: 'sales-order',
      ok: true,
      summary: { mode: 'release_hold', orderNo: 'SO-HOLD-1', result: 'released' },
      sections: {
        diagnosis: 'Hold on order SO-HOLD-1 has been successfully released.',
        availableActions: ['detail'],
        recommendedNextStep: 'Refresh the order detail to check the new status.',
        executionResult: { data: true }
      }
    })
  })

  it('explains hold rejection with no remaining quantity when release fails', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      releaseHold: async () => ({ data: false }),
      getManualAllocationItems: async () => ({
        data: {
          itemVOList: [
            { sku: 'SKU-A', totalQty: 1, allocated: 1, remaining: 0 },
            { sku: 'SKU-B', totalQty: 2, allocated: 2, remaining: 0 }
          ]
        }
      })
    })

    const result = await agent.execute({ type: 'release_hold', orderNo: 'SO-HOLD-2' })

    expect(result).toMatchObject({
      agent: 'sales-order',
      ok: false,
      summary: { mode: 'release_hold', orderNo: 'SO-HOLD-2', result: 'rejected' },
      sections: expect.objectContaining({
        diagnosis: expect.stringContaining('no unfulfilled quantity remaining'),
        recommendedNextStep: expect.stringContaining('manually in OMS')
      })
    })
  })

  it('blocks manual allocation when all items have remaining=0', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      checkManualAllocation: async () => ({ data: true }),
      getManualAllocationItems: async () => ({
        data: {
          itemVOList: [
            { sku: 'SKU-A', totalQty: 1, allocated: 1, remaining: 0 }
          ]
        }
      })
    })

    const result = await agent.execute({
      type: 'force-allocate-without-inventory-check',
      orderNo: 'SO-FULL-1',
      targetWarehouseNo: 'WH-001',
      confirmed: true
    })

    expect(result).toMatchObject({
      agent: 'sales-order',
      ok: false,
      summary: expect.objectContaining({ result: 'nothing_to_allocate' }),
      sections: expect.objectContaining({
        diagnosis: expect.stringContaining('already fully allocated')
      })
    })
  })

  it('uses plural form in diagnosis when multiple item lines are unallocated', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({
        data: {
          orderNo: 'SO-MULTI-1',
          status: 'EXCEPTION',
          warehouseId: null,
          itemLines: [
            { sku: 'SKU-A', qty: 2, allocatedQty: 0 },
            { sku: 'SKU-B', qty: 3, allocatedQty: 0 }
          ]
        }
      }),
      reopenSalesOrder: async () => ({})
    })

    const result = await agent.execute({ type: 'detail', orderNo: 'SO-MULTI-1' })

    expect(result).toMatchObject({
      sections: expect.objectContaining({
        diagnosis: expect.stringContaining('2 item lines have unallocated quantity'),
        signals: expect.arrayContaining([
          expect.stringContaining('2 item lines have qty greater than allocatedQty')
        ])
      })
    })
  })

  it('returns routing rules with structured agent response', async () => {
    const agent = createSalesOrderAgent({
      querySalesOrders: async () => ({ data: { records: [] } }),
      getSalesOrderDetail: async () => ({ data: {} }),
      reopenSalesOrder: async () => ({}),
      getRoutingRules: async () => ({
        data: [{ pageId: 1, pageName: 'Default Rules', isDefault: true, ruleItems: [] }]
      })
    })

    const result = await agent.execute({ type: 'get_routing_rules' })

    expect(result).toMatchObject({
      agent: 'sales-order',
      ok: true,
      summary: { mode: 'get_routing_rules', rulePageCount: 1 },
      sections: expect.objectContaining({
        routingRuleSummary: expect.objectContaining({
          pageCount: 1,
          activeRules: []
        }),
        routingRules: expect.arrayContaining([
          expect.objectContaining({ pageName: 'Default Rules' })
        ]),
        diagnosis: expect.stringContaining('dispatch strategy switches')
      })
    })
  })
})
