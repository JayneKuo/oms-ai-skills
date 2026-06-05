import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

const root = 'C:/Users/Jayne/Desktop/OMS AI SKILLS'

function read(relativePath: string) {
  return readFileSync(`${root}/${relativePath}`, 'utf8')
}

describe('phase-1 scope docs', () => {
  it('describe Sales Order Agent as the only implementation-first phase-1 agent', () => {
    const readme = read('README.md')
    const matrix = read('docs/agent-matrix.md')
    const phases = read('docs/implementation-phases.md')
    const architecture = read('docs/architecture.md')

    expect(readme).toContain('Sales Order Agent')
    expect(readme).toContain('Product Agent')
    expect(readme).toContain('Purchase Order Agent')

    expect(matrix).toContain('Sales Order Agent')
    expect(matrix).toContain('Product Agent')
    expect(matrix).toContain('Purchase Order Agent')
    expect(matrix).toContain('implementation-first')

    expect(phases).toContain('Sales Order Agent')
    expect(phases).toContain('documentation-only')

    expect(architecture).toContain('shared foundation')
    expect(architecture).toContain('multi-skill')
  })

  it('defines each agent with skills and output sections', () => {
    const sales = read('docs/sales-order-agent.md')
    const product = read('docs/product-agent.md')
    const purchase = read('docs/purchase-order-agent.md')
    const capability = read('docs/capability-status.md')

    expect(sales).toContain('sales-order-query')
    expect(sales).toContain('sales-order-reopen')
    expect(sales).toContain('Order Summary')
    expect(sales).toContain('Recommended Next Step')

    expect(product).toContain('product-query')
    expect(product).toContain('product-sync-channel')

    expect(purchase).toContain('purchase-order-query')
    expect(purchase).toContain('purchase-order-push-warehouse')

    expect(capability).toContain('Sales Order Agent')
    expect(capability).toContain('Product Agent')
    expect(capability).toContain('Purchase Order Agent')
    expect(capability).toContain('| Capability | Depends On | Status | Evidence | Gap | Target |')
  })
})
