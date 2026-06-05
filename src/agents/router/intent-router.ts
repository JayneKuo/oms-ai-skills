export function createIntentRouter() {
  return {
    route(input: string) {
      const normalized = input.toLowerCase()

      if (normalized.includes('dispatch log')) {
        return 'oms-query'
      }

      if (normalized.includes('sales order') || normalized.includes('sales-order')) {
        return 'sales-order'
      }

      return 'auth'
    }
  }
}
