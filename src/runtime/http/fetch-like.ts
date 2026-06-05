type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export function createNodeFetchLike(fetchImpl: FetchLike = fetch): FetchLike {
  return fetchImpl
}
