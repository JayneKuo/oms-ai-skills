type Bootstrap = {
  services: {
    iam: {
      getToken: () => Promise<unknown>
      getUserInfo: () => Promise<unknown>
    }
  }
}

export function createRunAuthSmoke(createBootstrap: () => Bootstrap) {
  return async () => {
    const bootstrap = createBootstrap()
    const token = await bootstrap.services.iam.getToken()
    const userInfo = await bootstrap.services.iam.getUserInfo()

    return {
      token,
      userInfo
    }
  }
}
