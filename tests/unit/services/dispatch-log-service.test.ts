import { describe, expect, it } from 'vitest'
import { createDispatchLogService } from '../../../src/services/dispatch/dispatch-log-service'

describe('createDispatchLogService', () => {
  it('queries dispatch log records by event id', async () => {
    const service = createDispatchLogService({
      get: async (path) => [{ path, status: 1 }]
    })

    const result = await service.getDispatchLog('EVT-1')

    expect(result).toEqual([{ path: '/api/linker-oms/oas/rpc-api/dispatch-log/EVT-1', status: 1 }])
  })
})
