import type { OmsEnv } from '../config/env'
import { createStagingBootstrap } from './bootstrap-staging'

type DispatchSmokeInput = {
  referenceNo: string
  orderNo: string
  items: unknown[]
  defaultRules: unknown[]
  customRules: unknown[]
}

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export async function runStagingDispatchSmoke(
  env: OmsEnv,
  input: DispatchSmokeInput,
  fetchImpl?: FetchLike
) {
  const bootstrap = createStagingBootstrap(env, fetchImpl)
  return bootstrap.services.dispatch.dispatchSalesOrder(input)
}
