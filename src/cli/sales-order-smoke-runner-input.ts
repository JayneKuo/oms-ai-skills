type EnvLike = {
  OMS_SALES_ORDER_MODE?: string
  OMS_SALES_ORDER_ORDER_NO?: string
  OMS_SALES_ORDER_PAGE_NO?: string
  OMS_SALES_ORDER_PAGE_SIZE?: string
  OMS_SALES_ORDER_KEYWORD?: string
  OMS_SALES_ORDER_CONFIRMED?: string
  OMS_SALES_ORDER_TARGET_WAREHOUSE_NO?: string
  OMS_SALES_ORDER_SKUS?: string  // JSON: [{"sku":"A","quantity":10}]
}

export function createSalesOrderSmokeInput(env: EnvLike) {
  const mode = env.OMS_SALES_ORDER_MODE ?? 'query'

  if (mode === 'release_hold') {
    if (!env.OMS_SALES_ORDER_ORDER_NO) {
      throw new Error('OMS_SALES_ORDER_ORDER_NO is required when OMS_SALES_ORDER_MODE=release_hold')
    }
    return { type: 'release_hold' as const, orderNo: env.OMS_SALES_ORDER_ORDER_NO }
  }

  if (mode === 'get_routing_rules') {
    return { type: 'get_routing_rules' as const }
  }

  if (mode === 'suggest_purchase_order') {
    if (!env.OMS_SALES_ORDER_SKUS) {
      throw new Error('OMS_SALES_ORDER_SKUS is required when OMS_SALES_ORDER_MODE=suggest_purchase_order (JSON array)')
    }
    return {
      type: 'suggest_purchase_order' as const,
      items: JSON.parse(env.OMS_SALES_ORDER_SKUS) as Array<{ sku: string; quantity: number }>
    }
  }

  if (mode === 'diagnose-exceptions') {
    return {
      type: 'diagnose-exceptions' as const,
      pageSize: Number(env.OMS_SALES_ORDER_PAGE_SIZE ?? '10')
    }
  }

  if (mode === 'force-allocate-without-inventory-check') {
    if (!env.OMS_SALES_ORDER_ORDER_NO) {
      throw new Error(
        'OMS_SALES_ORDER_ORDER_NO is required when OMS_SALES_ORDER_MODE=force-allocate-without-inventory-check'
      )
    }

    if (!env.OMS_SALES_ORDER_TARGET_WAREHOUSE_NO) {
      throw new Error(
        'OMS_SALES_ORDER_TARGET_WAREHOUSE_NO is required when OMS_SALES_ORDER_MODE=force-allocate-without-inventory-check'
      )
    }

    return {
      type: 'force-allocate-without-inventory-check' as const,
      orderNo: env.OMS_SALES_ORDER_ORDER_NO,
      targetWarehouseNo: env.OMS_SALES_ORDER_TARGET_WAREHOUSE_NO,
      confirmed: env.OMS_SALES_ORDER_CONFIRMED === 'true'
    }
  }

  if (mode === 'create_purchase_order') {
    if (!env.OMS_SALES_ORDER_TARGET_WAREHOUSE_NO) {
      throw new Error('OMS_SALES_ORDER_TARGET_WAREHOUSE_NO is required when OMS_SALES_ORDER_MODE=create_purchase_order')
    }
    if (!env.OMS_SALES_ORDER_SKUS) {
      throw new Error('OMS_SALES_ORDER_SKUS is required when OMS_SALES_ORDER_MODE=create_purchase_order (JSON array)')
    }
    return {
      type: 'create_purchase_order' as const,
      targetWarehouseNo: env.OMS_SALES_ORDER_TARGET_WAREHOUSE_NO,
      items: JSON.parse(env.OMS_SALES_ORDER_SKUS) as Array<{ sku: string; quantity: number }>
    }
  }

  if (mode === 'detail') {
    if (!env.OMS_SALES_ORDER_ORDER_NO) {
      throw new Error('OMS_SALES_ORDER_ORDER_NO is required when OMS_SALES_ORDER_MODE=detail')
    }

    return {
      type: 'detail' as const,
      orderNo: env.OMS_SALES_ORDER_ORDER_NO
    }
  }

  if (mode === 'reopen') {
    if (!env.OMS_SALES_ORDER_ORDER_NO) {
      throw new Error('OMS_SALES_ORDER_ORDER_NO is required when OMS_SALES_ORDER_MODE=reopen')
    }

    return {
      type: 'reopen' as const,
      orderNo: env.OMS_SALES_ORDER_ORDER_NO,
      confirmed: env.OMS_SALES_ORDER_CONFIRMED === 'true'
    }
  }

  return {
    type: 'query' as const,
    filters: {
      pageNo: Number(env.OMS_SALES_ORDER_PAGE_NO ?? '1'),
      pageSize: Number(env.OMS_SALES_ORDER_PAGE_SIZE ?? '20'),
      keyword: env.OMS_SALES_ORDER_KEYWORD
    }
  }
}
