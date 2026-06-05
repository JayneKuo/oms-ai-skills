import type { OmsEnv } from '../config/env'
import { createStagingBootstrap } from './bootstrap-staging'

type ShippingMappingInput = {
  channelId: number
  inputConditions: Record<string, string>
}

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export async function runStagingShippingMappingSmoke(
  env: OmsEnv,
  input: ShippingMappingInput,
  fetchImpl?: FetchLike
) {
  const bootstrap = createStagingBootstrap(env, fetchImpl)
  return bootstrap.services.mapping.executeShippingMapping(input)
}
