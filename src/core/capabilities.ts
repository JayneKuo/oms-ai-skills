const LEGACY_CAPABILITY_MAP: Record<string, string[]> = {
  auth: ['POST /iam/token', 'GET /iam/user-info'],
  'warehouse-allocation': ['POST /dispatch/sales-order'],
  'oms-query': ['GET /dispatch-log/{eventId}'],
  'shipping-rate': [
    'POST /mapping/shipping/execute',
    'POST /mapping/condition/execute',
    'GET /mapping/list'
  ]
}

export const CAPABILITY_ENDPOINTS = {
  'sales-order': [
    'sales-order-query',
    'sales-order-status-analysis',
    'allocation-rule-evaluator',
    'item-master-query',
    'inventory-query',
    'sales-order-reopen',
    'sales-order-manual-allocation',
    'sales-order-action-recommender'
  ],
  product: [
    'product-query',
    'product-create',
    'product-sync-channel',
    'product-diagnosis'
  ],
  'purchase-order': [
    'purchase-order-query',
    'purchase-order-create',
    'purchase-order-push-warehouse',
    'purchase-order-diagnosis'
  ]
} as const

export function listCapabilitiesByAgent(agentName: string): string[] {
  return LEGACY_CAPABILITY_MAP[agentName] ?? []
}
