type RegisteredAgent = {
  name: string
  execute: (input?: unknown) => Promise<unknown>
}

export function createAgentRegistry(agents: RegisteredAgent[]) {
  const byName = new Map(agents.map((agent) => [agent.name, agent]))

  return {
    get(name: string) {
      return byName.get(name)
    },
    list() {
      return [...byName.keys()]
    }
  }
}
