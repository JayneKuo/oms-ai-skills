export type DefinedService<TInput = unknown, TOutput = unknown> = {
  name: string
  execute: (input?: TInput) => Promise<TOutput>
}

export function defineService<TInput = unknown, TOutput = unknown>(service: DefinedService<TInput, TOutput>) {
  return service
}
