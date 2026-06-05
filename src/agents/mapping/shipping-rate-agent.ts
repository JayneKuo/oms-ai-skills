type MappingService = {
  executeShippingMapping: (input: { channelId: number; inputConditions: Record<string, unknown> }) => Promise<Record<string, unknown>>
}

export function createShippingRateAgent(service: MappingService) {
  return {
    name: 'shipping-rate',
    async execute(input: { channelId: number; inputConditions: Record<string, unknown> }) {
      const output = await service.executeShippingMapping(input)

      return {
        agent: 'shipping-rate',
        ok: true,
        summary: {
          outputKeys: Object.keys(output)
        },
        output
      }
    }
  }
}
