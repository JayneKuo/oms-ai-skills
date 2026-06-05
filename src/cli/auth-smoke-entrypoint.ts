import type { OmsEnv } from '../config/env'
import { createStagingBootstrap } from './bootstrap-staging'
import { createRunAuthSmoke } from './run-auth-smoke'

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export async function runStagingAuthSmoke(env: OmsEnv, fetchImpl?: FetchLike) {
  const bootstrap = createStagingBootstrap(env, fetchImpl)
  const runAuthSmoke = createRunAuthSmoke(() => ({
    services: {
      iam: {
        getToken: async () => ({ data: { accessToken: await bootstrap.runtime.tokenProvider.getAccessToken() } }),
        getUserInfo: () => bootstrap.services.iam.getUserInfo()
      }
    }
  }))

  return runAuthSmoke()
}
