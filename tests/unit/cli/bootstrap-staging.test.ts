import { describe, expect, it, vi } from 'vitest'
import { createStagingBootstrap } from '../../../src/cli/bootstrap-staging'

describe('createStagingBootstrap', () => {
  it('builds a staging-ready dependency graph from env values', () => {
    const bootstrap = createStagingBootstrap({
      OMS_BASE_URL: 'https://omsv2-staging.item.com',
      OMS_IAM_BASE_URL: 'https://id-staging.item.com',
      OMS_IAM_CLIENT_ID: 'client-id',
      OMS_TENANT_ID: 'LT',
      OMS_MERCHANT_NO: 'LAN0000002',
      OMS_USERNAME: 'test-user@example.com',
      OMS_PASSWORD: 'test-password'
    })

    expect(bootstrap.context).toEqual({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'client-id',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'test-user@example.com',
      password: 'test-password'
    })
    expect(bootstrap.services).toHaveProperty('iam')
    expect(bootstrap.services).toHaveProperty('dispatch')
    expect(bootstrap.services).toHaveProperty('dispatchLog')
    expect(bootstrap.services).toHaveProperty('mapping')
  })

  it('uses the provided fetch implementation for token and user-info calls', async () => {
    const fetchLike = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { accessToken: 'token-123' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { username: 'test-user@example.com' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )

    const bootstrap = createStagingBootstrap(
      {
        OMS_BASE_URL: 'https://omsv2-staging.item.com',
        OMS_IAM_BASE_URL: 'https://id-staging.item.com',
        OMS_IAM_CLIENT_ID: 'client-id',
        OMS_TENANT_ID: 'LT',
        OMS_MERCHANT_NO: 'LAN0000002',
        OMS_USERNAME: 'test-user@example.com',
        OMS_PASSWORD: 'test-password'
      },
      fetchLike
    )

    await expect(bootstrap.runtime.tokenProvider.getAccessToken()).resolves.toBe('token-123')
    await expect(bootstrap.services.iam.getUserInfo()).resolves.toEqual({
      data: { username: 'test-user@example.com' }
    })
    expect(fetchLike).toHaveBeenNthCalledWith(
      1,
      'https://omsv2-staging.item.com/api/linker-oms/opc/iam/token',
      expect.objectContaining({ method: 'POST' })
    )
    expect(fetchLike).toHaveBeenNthCalledWith(
      2,
      'https://omsv2-staging.item.com/api/iam/user-info',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: 'Bearer token-123' })
      })
    )
  })
})
