export type AgentResult<TSummary = unknown, TData = unknown> = {
  agent: string
  ok: boolean
  summary: TSummary
  data?: TData
}

export function createAgentResult<TSummary, TData = unknown>(
  agent: string,
  ok: boolean,
  summary: TSummary,
  data?: TData
): AgentResult<TSummary, TData> {
  return {
    agent,
    ok,
    summary,
    data
  }
}
