export type OmsEnv = {
  OMS_BASE_URL: string
  OMS_IAM_BASE_URL: string
  OMS_IAM_CLIENT_ID: string
  OMS_TENANT_ID: string
  OMS_MERCHANT_NO: string
  OMS_USERNAME: string
  OMS_PASSWORD: string
}

export function readOmsEnv(env: OmsEnv) {
  return {
    baseUrl: env.OMS_BASE_URL,
    iamBaseUrl: env.OMS_IAM_BASE_URL,
    iamClientId: env.OMS_IAM_CLIENT_ID,
    tenantId: env.OMS_TENANT_ID,
    merchantNo: env.OMS_MERCHANT_NO,
    username: env.OMS_USERNAME,
    password: env.OMS_PASSWORD
  }
}
