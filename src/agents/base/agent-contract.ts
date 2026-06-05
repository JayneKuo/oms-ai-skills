export type DefinedAgent<TInput = unknown, TOutput = unknown> = {
  name: string
  description: string
  execute: (input?: TInput) => Promise<TOutput>
}

export function defineAgent<TInput = unknown, TOutput = unknown>(agent: DefinedAgent<TInput, TOutput>) {
  return agent
}
