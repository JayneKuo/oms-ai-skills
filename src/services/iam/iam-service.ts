type IamClient = {
  get: (path: string) => Promise<unknown>
  post: (path: string, body: unknown) => Promise<unknown>
}

export function createIamService(client: IamClient) {
  return {
    async getUserInfo() {
      return client.get('/api/iam/user-info')
    },
    async getToken(body: Record<string, unknown>) {
      return client.post('/api/linker-oms/opc/iam/token', body)
    }
  }
}
