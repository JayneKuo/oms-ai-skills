import { describe, expect, it } from 'vitest'
import { createRunAuthSmoke } from '../../../src/cli/run-auth-smoke'

describe('createRunAuthSmoke', () => {
  it('executes token and user-info checks through the bootstrap services', async () => {
    const runAuthSmoke = createRunAuthSmoke(() => ({
      services: {
        iam: {
          getToken: async () => ({ data: { accessToken: 'token-123' } }),
          getUserInfo: async () => ({ data: { username: 'test-user@example.com' } })
        }
      }
    }))

    await expect(runAuthSmoke()).resolves.toEqual({
      token: { data: { accessToken: 'token-123' } },
      userInfo: { data: { username: 'test-user@example.com' } }
    })
  })
})
