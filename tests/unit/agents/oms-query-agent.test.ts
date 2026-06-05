import { describe, expect, it } from 'vitest'
import { createOmsQueryAgent } from '../../../src/agents/query/oms-query-agent'

describe('createOmsQueryAgent', () => {
  it('returns dispatch log records for an event id', async () => {
    const agent = createOmsQueryAgent({
      getDispatchLog: async (eventId: string) => [{ eventId, status: 1, summary: 'ok' }]
    })

    const result = await agent.execute({ eventId: 'EVT-1' })

    expect(result).toEqual({
      agent: 'oms-query',
      ok: true,
      summary: {
        eventId: 'EVT-1',
        recordCount: 1
      },
      records: [{ eventId: 'EVT-1', status: 1, summary: 'ok' }]
    })
  })
})
