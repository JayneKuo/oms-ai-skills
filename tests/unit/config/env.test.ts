import { describe, expect, it } from 'vitest'
import { readOmsEnv } from '../../../src/config/env'

describe('readOmsEnv', () => {
  it('reads required OMS settings from an env-like object', () => {
    const env = readOmsEnv({
      OMS_BASE_URL: 'https://omsv2-staging.item.com',
      OMS_IAM_BASE_URL: 'https://id-staging.item.com',
      OMS_IAM_CLIENT_ID: 'client-id',
      OMS_TENANT_ID: 'LT',
      OMS_MERCHANT_NO: 'LAN0000002',
      OMS_USERNAME: 'test-user@example.com',
      OMS_PASSWORD: 'test-password'
    })

    expect(env).toEqual({
      baseUrl: 'https://omsv2-staging.item.com',
      iamBaseUrl: 'https://id-staging.item.com',
      iamClientId: 'client-id',
      tenantId: 'LT',
      merchantNo: 'LAN0000002',
      username: 'test-user@example.com',
      password: 'test-password'
    })
  })
})
