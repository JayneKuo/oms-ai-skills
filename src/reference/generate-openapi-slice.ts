import { WAVE1_ENDPOINTS } from './wave1-endpoints'

type OpenApiLike = {
  openapi?: string
  info?: unknown
  paths?: Record<string, unknown>
}

export function generateWave1OpenApiSlice(source: OpenApiLike) {
  const selectedPaths = Object.fromEntries(
    WAVE1_ENDPOINTS.filter((path) => source.paths?.[path] !== undefined).map((path) => [path, source.paths?.[path]])
  )

  return {
    openapi: source.openapi ?? '3.0.1',
    info: source.info ?? { title: 'Wave 1 OMS Slice' },
    paths: selectedPaths
  }
}
