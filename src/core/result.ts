export type OkResult<T> = {
  ok: true
  data: T
}

export type FailResult = {
  ok: false
  error: string
}

export function okResult<T>(data: T): OkResult<T> {
  return { ok: true, data }
}

export function failResult(error: string): FailResult {
  return { ok: false, error }
}
