import type { OmsContext } from '../../config/oms-context'

type MappingClient = {
  get: (path: string, query?: Record<string, unknown>) => Promise<unknown>
  post: (path: string, body: unknown) => Promise<unknown>
}

export function createMappingService(_context: OmsContext, client: MappingClient) {
  return {
    async listMappings(query: Record<string, unknown>) {
      return client.get('/api/linker-oms/oas/rpc-api/mapping/list', query)
    },
    async executeShippingMapping(body: Record<string, unknown>) {
      return client.post('/api/linker-oms/oas/rpc-api/mapping/shipping/execute', body)
    },
    async executeConditionMapping(body: Record<string, unknown>) {
      return client.post('/api/linker-oms/oas/rpc-api/mapping/condition/execute', body)
    }
  }
}
