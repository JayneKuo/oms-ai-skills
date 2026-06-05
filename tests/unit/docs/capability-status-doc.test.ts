import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

const root = 'C:/Users/Jayne/Desktop/OMS AI SKILLS'

function read(relativePath: string) {
  return readFileSync(`${root}/${relativePath}`, 'utf8')
}

describe('capability-status documentation', () => {
  it('uses explicit status levels and release-readiness sections', () => {
    const foundation = read('docs/foundation.md')
    const release = read('docs/release-readiness.md')
    const interaction = read('docs/agent-interaction.md')
    const testing = read('docs/testing-strategy.md')

    expect(foundation).toContain('not a separately published skill')
    expect(release).toContain('Planned')
    expect(release).toContain('Discovered')
    expect(release).toContain('Implemented')
    expect(release).toContain('Validated')
    expect(release).toContain('Production-ready')
    expect(release).toContain('Sales Order Agent')
    expect(release).toContain('Product Agent')
    expect(release).toContain('Purchase Order Agent')
    expect(interaction).toContain('agent prompt')
    expect(interaction).toContain('skill')
    expect(testing).toContain('Sales Order Agent')
  })

  it('documents the discovery requirement for sales-order dependencies', () => {
    const apiScope = read('docs/api-scope.md')
    const discovery = read('docs/sales-order-api-discovery.md')

    expect(apiScope).toContain('Sales Order Agent implementation scope')
    expect(apiScope).toContain('allocation rules')
    expect(apiScope).toContain('item master')
    expect(apiScope).toContain('inventory')

    expect(discovery).toContain('sales-order-query')
    expect(discovery).toContain('sales-order-reopen')
    expect(discovery).toContain('sales-order-manual-allocation')
    expect(discovery).toContain('allocation-rule-evaluator')
    expect(discovery).toContain('item-master-query')
    expect(discovery).toContain('inventory-query')
  })
})
