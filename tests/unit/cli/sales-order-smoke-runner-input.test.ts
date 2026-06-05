import { describe, expect, it } from 'vitest'
import { createSalesOrderSmokeInput } from '../../../src/cli/sales-order-smoke-runner-input'

describe('createSalesOrderSmokeInput', () => {
  it('builds query mode from env-like values by default', () => {
    expect(
      createSalesOrderSmokeInput({
        OMS_SALES_ORDER_PAGE_NO: '2',
        OMS_SALES_ORDER_PAGE_SIZE: '50',
        OMS_SALES_ORDER_KEYWORD: 'SO'
      })
    ).toEqual({
      type: 'query',
      filters: {
        pageNo: 2,
        pageSize: 50,
        keyword: 'SO'
      }
    })
  })

  it('builds exception diagnosis mode when OMS_SALES_ORDER_MODE=diagnose-exceptions', () => {
    expect(
      createSalesOrderSmokeInput({
        OMS_SALES_ORDER_MODE: 'diagnose-exceptions',
        OMS_SALES_ORDER_PAGE_SIZE: '3'
      })
    ).toEqual({
      type: 'diagnose-exceptions',
      pageSize: 3
    })
  })

  it('builds force allocation mode when inventory validation is skipped', () => {
    expect(
      createSalesOrderSmokeInput({
        OMS_SALES_ORDER_MODE: 'force-allocate-without-inventory-check',
        OMS_SALES_ORDER_ORDER_NO: 'SO-ALLOC-1',
        OMS_SALES_ORDER_TARGET_WAREHOUSE_NO: 'WH-001'
      })
    ).toEqual({
      type: 'force-allocate-without-inventory-check',
      orderNo: 'SO-ALLOC-1',
      targetWarehouseNo: 'WH-001',
      confirmed: false
    })
  })

  it('builds detail mode when OMS_SALES_ORDER_MODE=detail', () => {
    expect(
      createSalesOrderSmokeInput({
        OMS_SALES_ORDER_MODE: 'detail',
        OMS_SALES_ORDER_ORDER_NO: 'SO-500'
      })
    ).toEqual({
      type: 'detail',
      orderNo: 'SO-500'
    })
  })

  it('builds reopen mode when OMS_SALES_ORDER_MODE=reopen and confirmed=true', () => {
    expect(
      createSalesOrderSmokeInput({
        OMS_SALES_ORDER_MODE: 'reopen',
        OMS_SALES_ORDER_ORDER_NO: 'SO-600',
        OMS_SALES_ORDER_CONFIRMED: 'true'
      })
    ).toEqual({
      type: 'reopen',
      orderNo: 'SO-600',
      confirmed: true
    })
  })

  it('does not auto-confirm reopen mode', () => {
    expect(
      createSalesOrderSmokeInput({
        OMS_SALES_ORDER_MODE: 'reopen',
        OMS_SALES_ORDER_ORDER_NO: 'SO-600'
      })
    ).toEqual({
      type: 'reopen',
      orderNo: 'SO-600',
      confirmed: false
    })
  })

  it('requires orderNo for detail and reopen modes', () => {
    expect(() => createSalesOrderSmokeInput({ OMS_SALES_ORDER_MODE: 'detail' })).toThrow(
      'OMS_SALES_ORDER_ORDER_NO is required when OMS_SALES_ORDER_MODE=detail'
    )
    expect(() => createSalesOrderSmokeInput({ OMS_SALES_ORDER_MODE: 'reopen' })).toThrow(
      'OMS_SALES_ORDER_ORDER_NO is required when OMS_SALES_ORDER_MODE=reopen'
    )
  })
})
