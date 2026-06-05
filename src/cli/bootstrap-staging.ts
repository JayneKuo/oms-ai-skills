import { readOmsEnv } from '../config/env'
import { createOmsContext } from '../config/oms-context'
import { createTokenProvider } from '../runtime/auth/token-provider'
import { createNodeFetchLike } from '../runtime/http/fetch-like'
import { createOmsClient } from '../runtime/http/oms-client'
import { createIamService } from '../services/iam/iam-service'
import { createDispatchService } from '../services/dispatch/dispatch-service'
import { createDispatchLogService } from '../services/dispatch/dispatch-log-service'
import { createMappingService } from '../services/mapping/mapping-service'
import { createSalesOrderService } from '../services/sales-order/sales-order-service'

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export function createStagingBootstrap(
  envLike: {
    OMS_BASE_URL: string
    OMS_IAM_BASE_URL: string
    OMS_IAM_CLIENT_ID: string
    OMS_TENANT_ID: string
    OMS_MERCHANT_NO: string
    OMS_USERNAME: string
    OMS_PASSWORD: string
  },
  fetchImpl?: FetchLike
) {
  const env = readOmsEnv(envLike)
  const context = createOmsContext(env)
  const fetchLike = createNodeFetchLike(fetchImpl)
  const tokenProvider = createTokenProvider(context, fetchLike)
  const client = createOmsClient(context, () => tokenProvider.getAccessToken(), fetchLike)

  return {
    context,
    runtime: {
      fetchLike,
      tokenProvider,
      client
    },
    services: {
      iam: createIamService(client),
      dispatch: createDispatchService(context, client),
      dispatchLog: createDispatchLogService(client),
      mapping: createMappingService(context, client),
      salesOrder: createSalesOrderService(context, client)
    }
  }
}
