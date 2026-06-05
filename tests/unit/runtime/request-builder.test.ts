import { describe, expect, it } from 'vitest'
import { createRequestBuilder } from '../../../src/runtime/http/request-builder'

describe('createRequestBuilder', () => {
  it('adds tenant header and dispatch payload defaults', () => {
    const builder = createRequestBuilder({ tenantId: 'LT', merchantNo: 'LAN0000002' })

    const request = builder.buildPost('/dispatch/sales-order', {
      referenceNo: 'REF-1',
      orderNo: 'SO-1'
    })

    expect(request).toEqual({
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'LT'
      },
      body: {
        tenantId: 'LT',
        merchantNo: 'LAN0000002',
        referenceNo: 'REF-1',
        orderNo: 'SO-1'
      }
    })
  })
})
