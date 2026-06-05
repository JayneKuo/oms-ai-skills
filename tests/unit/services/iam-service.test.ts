import { describe, expect, it } from 'vitest'
import { createIamService } from '../../../src/services/iam/iam-service'

describe('createIamService', () => {
  it('reads current user info from the OMS client', async () => {
    const service = createIamService({
      get: async (path) => ({ path, data: { username: 'test-user@example.com' } }),
      post: async () => ({})
    })

    const result = await service.getUserInfo()

    expect(result).toEqual({ path: '/api/iam/user-info', data: { username: 'test-user@example.com' } })
  })
})
