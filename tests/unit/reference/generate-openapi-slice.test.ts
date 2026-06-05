import { describe, expect, it } from 'vitest'
import { generateWave1OpenApiSlice } from '../../../src/reference/generate-openapi-slice'

describe('generateWave1OpenApiSlice', () => {
  it('keeps only the approved Wave 1 endpoints from a larger OpenAPI document', () => {
    const source = {
      openapi: '3.0.1',
      paths: {
        '/iam/token': { post: { summary: 'token' } },
        '/dispatch/sales-order': { post: { summary: 'dispatch' } },
        '/dispatch-log/{eventId}': { get: { summary: 'query log' } },
        '/mapping/list': { get: { summary: 'mapping list' } },
        '/not-needed': { get: { summary: 'ignore' } }
      }
    }

    const slice = generateWave1OpenApiSlice(source)

    expect(Object.keys(slice.paths)).toEqual([
      '/iam/token',
      '/dispatch/sales-order',
      '/dispatch-log/{eventId}',
      '/mapping/list'
    ])
    expect(slice.paths['/not-needed']).toBeUndefined()
  })
})
