type RegistryLike = {
  get: (name: string) => { execute: (input?: unknown) => Promise<unknown> } | undefined
}

export async function runAgentByName(registry: RegistryLike, name: string, input?: unknown) {
  const agent = registry.get(name)

  if (!agent) {
    throw new Error(`Unknown agent: ${name}`)
  }

  return agent.execute(input)
}
