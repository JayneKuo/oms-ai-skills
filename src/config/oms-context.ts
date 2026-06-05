export type OmsContext = {
  baseUrl: string
  iamBaseUrl: string
  iamClientId: string
  tenantId: string
  merchantNo: string
  username: string
  password: string
}

export function createOmsContext(context: OmsContext): OmsContext {
  return context
}
