type ClientContext = {
  baseUrl: string
  tenantId: string
  merchantNo: string
}

type TokenProvider = () => Promise<string>
type FetchLike = (url: string, init?: RequestInit) => Promise<Response>

export function createOmsClient(context: ClientContext, getAccessToken: TokenProvider, fetchLike: FetchLike) {
  return {
    async get(path: string, query?: Record<string, unknown>) {
      const token = await getAccessToken()
      const search = new URLSearchParams()

      if (query) {
        for (const [key, value] of Object.entries(query)) {
          if (value === undefined) {
            continue
          }

          if (Array.isArray(value)) {
            for (const item of value) {
              search.append(key, String(item))
            }
            continue
          }

          search.append(key, String(value))
        }
      }

      const querySuffix = search.size > 0 ? `?${search.toString()}` : ''
      const response = await fetchLike(`${context.baseUrl}${path}${querySuffix}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'x-tenant-id': context.tenantId
        }
      })

      return response.json()
    },
    async post(path: string, body: unknown) {
      const token = await getAccessToken()
      const response = await fetchLike(`${context.baseUrl}${path}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'x-tenant-id': context.tenantId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      })

      return response.json()
    }
  }
}
