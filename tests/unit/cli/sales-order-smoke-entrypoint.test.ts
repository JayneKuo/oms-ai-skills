import { describe, expect, it, vi } from 'vitest'
import { runStagingSalesOrderSmoke } from '../../../src/cli/sales-order-smoke-entrypoint'

describe('runStagingSalesOrderSmoke', () => {
  it('queries sales orders through the staging bootstrap and returns the publishable sales-order output', async () => {
    const fetchLike = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: { access_token: 'token-123' } }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              records: [
                { orderNo: 'SO-1', status: 'OPEN' },
                { orderNo: 'SO-2', status: 'EXCEPTION' }
              ]
            }
          }),
          {
            headers: { 'Content-Type': 'application/json' }
          }
        )
      )

    await expect(
      runStagingSalesOrderSmoke(
        {
          OMS_BASE_URL: 'https://omsv2-staging.item.com',
          OMS_IAM_BASE_URL: 'https://id-staging.item.com',
          OMS_IAM_CLIENT_ID: 'client-id',
          OMS_TENANT_ID: 'LT',
          OMS_MERCHANT_NO: 'LAN0000002',
          OMS_USERNAME: 'test-user@example.com',
          OMS_PASSWORD: 'test-password'
        },
        {
          type: 'query',
          filters: {
            pageNo: 1,
            pageSize: 20,
            keyword: 'SO'
          }
        },
        fetchLike
      )
    ).resolves.toEqual({
      agent: 'sales-order',
      ok: true,
      summary: {
        mode: 'query',
        totalRecords: 2,
        orders: [
          { orderNo: 'SO-1', status: 'OPEN' },
          { orderNo: 'SO-2', status: 'EXCEPTION' }
        ]
      },
      sections: {
        orderSummary: {
          totalRecords: 2,
          orders: [
            { orderNo: 'SO-1', status: 'OPEN' },
            { orderNo: 'SO-2', status: 'EXCEPTION' }
          ]
        },
        diagnosis: 'Found 2 matching sales orders.',
        availableActions: ['detail'],
        recommendedNextStep: 'Review an order from the result set for detailed diagnosis or action.',
        executionResult: null
      }
    })

    expect(fetchLike.mock.calls[1]?.[0]).toContain(
      'https://omsv2-staging.item.com/api/linker-oms/opc/app-api/sale-order/page?'
    )
    expect(fetchLike.mock.calls[1]?.[0]).toContain('pageNo=1')
    expect(fetchLike.mock.calls[1]?.[0]).toContain('pageSize=20')
    expect(fetchLike.mock.calls[1]?.[0]).toContain('merchantNo=LAN0000002')
    expect(fetchLike.mock.calls[1]?.[0]).toContain('keyword=SO')
    expect(fetchLike).toHaveBeenNthCalledWith(
      2,
      expect.any(String),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ Authorization: 'Bearer token-123' })
      })
    )
  })
})
