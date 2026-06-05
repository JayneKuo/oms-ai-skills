type DispatchLogClient = {
  get: (path: string) => Promise<unknown>
}

export function createDispatchLogService(client: DispatchLogClient) {
  return {
    async getDispatchLog(eventId: string) {
      return client.get(`/api/linker-oms/oas/rpc-api/dispatch-log/${eventId}`)
    }
  }
}
