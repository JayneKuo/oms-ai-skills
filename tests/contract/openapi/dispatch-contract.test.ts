import { describe, expect, it } from 'vitest'
import { generateWave1OpenApiSlice } from '../../../src/reference/generate-openapi-slice'

describe('dispatch OpenAPI contract slice', () => {
  it('includes the sales-order dispatch and dispatch-log endpoints', () => {
    const openapi = generateWave1OpenApiSlice({
      paths: {
        '/dispatch/sales-order': { post: { summary: 'dispatch sales order' } },
        '/dispatch-log/{eventId}': { get: { summary: 'query dispatch log' } },
        '/not-needed': { get: { summary: 'ignore' } }
      }
    })

    expect(openapi.paths['/dispatch/sales-order']).toBeDefined()
    expect(openapi.paths['/dispatch-log/{eventId}']).toBeDefined()
    expect(openapi.paths['/not-needed']).toBeUndefined()
  })
})
