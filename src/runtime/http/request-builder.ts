type BuilderContext = {
  tenantId: string
  merchantNo: string
}

export function createRequestBuilder(context: BuilderContext) {
  return {
    buildPost(path: string, body: Record<string, unknown>) {
      const payload = path.startsWith('/dispatch/')
        ? {
            tenantId: context.tenantId,
            merchantNo: context.merchantNo,
            ...body
          }
        : body

      return {
        headers: {
          'Content-Type': 'application/json',
          'x-tenant-id': context.tenantId
        },
        body: payload
      }
    }
  }
}
