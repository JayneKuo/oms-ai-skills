import type { OmsContext } from '../../config/oms-context'

type FetchLike = (url: string, init?: RequestInit) => Promise<Response>

export function createTokenProvider(context: OmsContext, fetchLike: FetchLike) {
  let cachedToken: string | undefined

  return {
    async getAccessToken(): Promise<string> {
      if (cachedToken) {
        return cachedToken
      }

      const response = await fetchLike(`${context.baseUrl}/api/linker-oms/opc/iam/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-tenant-id': context.tenantId
        },
        body: JSON.stringify({
          grantType: 'password',
          username: context.username,
          password: context.password
        })
      })

      const payload = (await response.json()) as {
        data?: { accessToken?: string; access_token?: string }
      }
      const token = payload.data?.accessToken ?? payload.data?.access_token

      if (!token) {
        throw new Error('OMS token response missing access token')
      }

      cachedToken = token
      return token
    }
  }
}
