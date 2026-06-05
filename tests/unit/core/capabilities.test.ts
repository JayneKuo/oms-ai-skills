import { describe, expect, it } from 'vitest'
import { listCapabilitiesByAgent } from '../../../src/core/capabilities'

describe('listCapabilitiesByAgent', () => {
  it('returns declared Wave 1 capability ownership', () => {
    expect(listCapabilitiesByAgent('warehouse-allocation')).toEqual([
      'POST /dispatch/sales-order'
    ])
  })
})
