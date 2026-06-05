import { describe, expect, it } from 'vitest'
import { createDispatchLogService } from '../../../src/services/dispatch/dispatch-log-service'

describe('createDispatchLogService pathing', () => {
  it('requests dispatch logs from the staging RPC path', async () => {
    let capturedPath: string | undefined

    const service = createDispatchLogService({
      get: async (path) => {
        capturedPath = path
        return []
      }
    })

    await service.getDispatchLog('evt-123')

    expect(capturedPath).toBe('/api/linker-oms/oas/rpc-api/dispatch-log/evt-123')
  })
})
