import { describe, expect, it } from 'vitest'
import {
  PHASE1_SCOPE_ENDPOINT_FAMILIES,
  WAVE1_ENDPOINTS
} from '../../../src/reference/wave1-endpoints'
import { CAPABILITY_ENDPOINTS } from '../../../src/core/capabilities'

describe('wave1 endpoints', () => {
  it('preserves generator paths and tracks sales-order-first phase-one scope', () => {
    expect(WAVE1_ENDPOINTS).toEqual([
      '/iam/token',
      '/dispatch/sales-order',
      '/dispatch-log/{eventId}',
      '/mapping/list'
    ])

    expect(PHASE1_SCOPE_ENDPOINT_FAMILIES).toEqual([
      'POST /iam/token',
      'GET /iam/user-info',
      'sales-order list/detail endpoint family',
      'reopen action endpoint family',
      'manual allocation endpoint family',
      'allocation rules endpoint family',
      'item master endpoint family',
      'inventory endpoint family'
    ])

    expect(CAPABILITY_ENDPOINTS['sales-order']).toEqual([
      'sales-order-query',
      'sales-order-status-analysis',
      'allocation-rule-evaluator',
      'item-master-query',
      'inventory-query',
      'sales-order-reopen',
      'sales-order-manual-allocation',
      'sales-order-action-recommender'
    ])
  })
})
