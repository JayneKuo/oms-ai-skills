import { describe, expect, it } from 'vitest'
import { createShippingRateAgent } from '../../../src/agents/mapping/shipping-rate-agent'

describe('createShippingRateAgent', () => {
  it('executes shipping mapping and returns normalized output', async () => {
    const agent = createShippingRateAgent({
      executeShippingMapping: async () => ({ carrier: 'FedEx', shipMethod: 'Ground' })
    })

    const result = await agent.execute({
      channelId: 1,
      inputConditions: { carrier: 'FedEx' }
    })

    expect(result).toEqual({
      agent: 'shipping-rate',
      ok: true,
      summary: {
        outputKeys: ['carrier', 'shipMethod']
      },
      output: {
        carrier: 'FedEx',
        shipMethod: 'Ground'
      }
    })
  })
})
