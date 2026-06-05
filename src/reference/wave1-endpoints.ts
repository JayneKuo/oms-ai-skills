export const WAVE1_ENDPOINTS = [
  '/iam/token',
  '/dispatch/sales-order',
  '/dispatch-log/{eventId}',
  '/mapping/list'
] as const

export const PHASE1_SCOPE_ENDPOINT_FAMILIES = [
  'POST /iam/token',
  'GET /iam/user-info',
  'sales-order list/detail endpoint family',
  'reopen action endpoint family',
  'manual allocation endpoint family',
  'allocation rules endpoint family',
  'item master endpoint family',
  'inventory endpoint family'
] as const
