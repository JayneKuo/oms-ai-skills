import { describe, expect, it } from 'vitest'
import { createIntentRouter } from '../../../src/agents/router/intent-router'

describe('createIntentRouter sales-order routing', () => {
  it('routes sales-order prompts to the sales-order agent', () => {
    const router = createIntentRouter()

    expect(router.route('check sales order SO-100 status')).toBe('sales-order')
    expect(router.route('reopen sales order SO-100')).toBe('sales-order')
  })
})
