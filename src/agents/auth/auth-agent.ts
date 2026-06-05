type AuthService = {
  getToken: () => Promise<{ data?: { accessToken?: string } }>
  getUserInfo: () => Promise<{ data?: { username?: string } }>
}

export function createAuthAgent(service: AuthService) {
  return {
    name: 'auth',
    async execute() {
      const token = await service.getToken()
      const user = await service.getUserInfo()

      return {
        agent: 'auth',
        ok: true,
        summary: {
          hasToken: Boolean(token.data?.accessToken),
          username: user.data?.username
        }
      }
    }
  }
}
