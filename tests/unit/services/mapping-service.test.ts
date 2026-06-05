import { describe, expect, it } from 'vitest'
import { createOmsContext } from '../../../src/config/oms-context'
import { createMappingService } from '../../../src/services/mapping/mapping-service'

describe('createMappingService', () => {
  it('queries mapping list with tenant header defaults handled by the client layer', async () => {
    const context = createOmsContext({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'client',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'user',
      password: 'pass'
    })

    let captured: unknown
    const service = createMappingService(context, {
      get: async (path, query) => {
        captured = { path, query }
        return { data: [] }
      },
      post: async () => ({})
    })

    await service.listMappings({ mappingType: 'SKU' })

    expect(captured).toEqual({
      path: '/api/linker-oms/oas/rpc-api/mapping/list',
      query: { mappingType: 'SKU' }
    })
  })
})
