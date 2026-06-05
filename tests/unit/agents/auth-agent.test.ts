import { describe, expect, it } from 'vitest'
import { createAuthAgent } from '../../../src/agents/auth/auth-agent'

describe('createAuthAgent', () => {
  it('returns a normalized auth summary from IAM services', async () => {
    const agent = createAuthAgent({
      getToken: async () => ({ data: { accessToken: 'token-123' } }),
      getUserInfo: async () => ({ data: { username: 'test-user@example.com' } })
    })

    const result = await agent.execute()

    expect(result).toEqual({
      agent: 'auth',
      ok: true,
      summary: {
        hasToken: true,
        username: 'test-user@example.com'
      }
    })
  })
})
