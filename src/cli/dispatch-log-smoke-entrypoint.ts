import type { OmsEnv } from '../config/env'
import { createStagingBootstrap } from './bootstrap-staging'

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export async function runStagingDispatchLogSmoke(
  env: OmsEnv,
  eventId: string,
  fetchImpl?: FetchLike
) {
  const bootstrap = createStagingBootstrap(env, fetchImpl)
  return bootstrap.services.dispatchLog.getDispatchLog(eventId)
}
