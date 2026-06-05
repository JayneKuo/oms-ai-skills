import { describe, expect, it } from 'vitest'
import { createIntentRouter } from '../../../src/agents/router/intent-router'

describe('createIntentRouter', () => {
  it('routes dispatch-log intents to the oms-query agent', () => {
    const router = createIntentRouter()

    expect(router.route('query dispatch log for EVT-1')).toBe('oms-query')
  })
})
