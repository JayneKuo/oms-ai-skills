import { describe, expect, it } from 'vitest'
import { createNodeFetchLike } from '../../../src/runtime/http/fetch-like'

describe('createNodeFetchLike', () => {
  it('returns a function reference to the global fetch implementation', async () => {
    const fetchLike = createNodeFetchLike(async () => new Response('{}'))
    const response = await fetchLike('https://example.com')

    expect(response).toBeInstanceOf(Response)
  })
})
