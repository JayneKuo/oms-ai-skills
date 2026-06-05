const creds = { username: 'test-user@example.com', password: 'test-password' }

async function getToken(baseUrl: string) {
  const response = await fetch(`${baseUrl}/api/linker-oms/opc/iam/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-tenant-id': 'LT'
    },
    body: JSON.stringify({ grantType: 'password', ...creds })
  })

  const json = (await response.json()) as {
    data?: { accessToken?: string; access_token?: string }
  }

  return json.data?.accessToken ?? json.data?.access_token ?? ''
}

const hosts = ['https://omsv2-staging.item.com', 'https://di-v3-staging.item.com']
const paths = [
  '/rpc-api/sales-order/page?pageNo=1&pageSize=5&merchantNo=LAN0000002',
  '/app-api/sale-order/page?pageNo=1&pageSize=5&merchantNo=LAN0000002',
  '/api/linker-oms/oas/rpc-api/sales-order/page?pageNo=1&pageSize=5&merchantNo=LAN0000002',
  '/api/linker-oms/oas/app-api/sale-order/page?pageNo=1&pageSize=5&merchantNo=LAN0000002',
  '/api/linker-oms/opc/app-api/sale-order/page?pageNo=1&pageSize=5&merchantNo=LAN0000002',
  '/api/linker-oms/opc/app-api/sale-order/SO01385247',
  '/api/linker-oms/opc/app-api/sale-order/status/num?merchantNo=LAN0000002&statuses=ON_HOLD',
  '/api/linker-oms/opc/app-api/sale-order/status/num?merchantNo=LAN0000002&statuses=EXCEPTION'
]

for (const host of hosts) {
  try {
    const token = await getToken(host)

    console.log(`HOST=${host}`)
    for (const path of paths) {
      const response = await fetch(`${host}${path}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'x-tenant-id': 'LT',
          USER: 'test-user@example.com'
        }
      })
      const text = await response.text()
      console.log(
        JSON.stringify(
          {
            path,
            status: response.status,
            contentType: response.headers.get('content-type'),
            startsWith: text.slice(0, 120)
          },
          null,
          2
        )
      )
    }
  } catch (error) {
    console.log(`HOST=${host}`)
    console.log(JSON.stringify({ error: error instanceof Error ? error.message : String(error) }, null, 2))
  }
}
