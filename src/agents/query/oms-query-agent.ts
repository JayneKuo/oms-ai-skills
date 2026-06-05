type DispatchLogRecord = {
  eventId: string
  status: number
  summary: string
}

type DispatchLogService = {
  getDispatchLog: (eventId: string) => Promise<DispatchLogRecord[]>
}

export function createOmsQueryAgent(service: DispatchLogService) {
  return {
    async execute(input: { eventId: string }) {
      const records = await service.getDispatchLog(input.eventId)

      return {
        agent: 'oms-query',
        ok: true,
        summary: {
          eventId: input.eventId,
          recordCount: records.length
        },
        records
      }
    }
  }
}
