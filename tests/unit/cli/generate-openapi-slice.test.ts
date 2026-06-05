import { describe, expect, it } from 'vitest'
import { createOpenApiSliceGenerator } from '../../../src/cli/generate-openapi-slice'

describe('createOpenApiSliceGenerator', () => {
  it('writes a generated Wave 1 slice to the target file', () => {
    let writtenPath = ''
    let writtenText = ''

    const generate = createOpenApiSliceGenerator({
      readFile: () => JSON.stringify({
        openapi: '3.0.1',
        paths: {
          '/iam/token': { post: { summary: 'token' } },
          '/not-needed': { get: { summary: 'ignore' } }
        }
      }),
      writeFile: (path, text) => {
        writtenPath = path
        writtenText = text
      }
    })

    generate('source.json', 'out.json')

    expect(writtenPath).toBe('out.json')
    expect(JSON.parse(writtenText)).toEqual({
      openapi: '3.0.1',
      info: { title: 'Wave 1 OMS Slice' },
      paths: {
        '/iam/token': { post: { summary: 'token' } }
      }
    })
  })
})
